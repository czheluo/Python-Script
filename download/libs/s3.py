# -*- coding: utf-8 -*-
# __author__ = 'guoquan'
from filechunkio import FileChunkIO
import threading
from threading import Thread, Lock
from Queue import Queue
import copy
import re
from boto.s3.bucket import Bucket, Key
import gevent
import os
import sqlite3
import math
import traceback
import sys
from .config import Config
import datetime
try:
    import xattr
except:
    pass
import traceback


class TransferFailedError(Exception):
    """
    文件传输失败时触发
    """
    def __init__(self, value):
        Exception.__init__(self, value)
        self.value = value

    def __str__(self):
        return str(self.value)


class TransferError(Exception):
    """
    文件传输失败时触发
    """
    def __init__(self, value):
        Exception.__init__(self, value)
        self.value = value

    def __str__(self):
        return str(self.value)


def friendly_size(size):
    gb = 1024 * 1024 * 1024
    mb = 1024 * 1024
    kb = 1024
    if size >= gb:
        return "%sG" % (size*1.0 / gb)
    elif size >= mb:
        return "%sM" % (size*1.0 / mb)
    elif size >= kb:
        return "%sK" % (size*1.0 / kb)
    else:
        return "%s/b" % size


class S3TransferManager(object):
    def __init__(self, base_path=None, use_db=False, overwrite=True, log=True, etag=0, bcl_type="tsg"):
        self.config = Config()
        self._conn = None
        self._max_threads = self.config.get_rgw_max_threads()
        self.base_path = os.path.abspath(base_path) if base_path else os.getcwd()
        self._call_back = None
        self._use_db = use_db
        self._files = {}
        self.overwrite = overwrite
        self._start_time = None
        self._count_bytes = 0
        self.log = log
        self.etag = etag
        self.file_queue = Queue(2000)
        self._end = False
        self._threads = []
        self.main_thread = threading.current_thread()
        self.bcl_type = bcl_type

    def update(self, size):
        self._count_bytes += size

    @property
    def speed(self):
        if self._start_time:
            second = (datetime.datetime.now() - self._start_time).seconds
            if second == 0:
                second = 1
            data = "%s/s" % friendly_size(self._count_bytes*1.0/second)
            if second > 600:
                self._start_time = datetime.datetime.now()
                self._count_bytes = 0
            return data
        else:
            return 0

    @property
    def running(self):
        i = 0
        for key, f in self._files.items():
            if not f.is_end:
                i += 1
            else:
                if f.finish:
                    self._files.pop(key)
        return i

    @property
    def files(self):
        return self._files

    @property
    def use_db(self):
        return self._use_db

    @property
    def callback(self):
        return self._call_back

    @callback.setter
    def callback(self, func):
        self._call_back = func

    def add(self, from_uri, to_uri=None):
        if os.path.exists(from_uri):
            if os.path.exists("%s.s3db" % from_uri):
                if self.use_db:
                    self.add_continue(from_uri)
                else:
                    os.remove("%s.s3db" % from_uri)
                    self.add_new_file(from_uri, to_uri)
            else:
                self.add_new_file(from_uri, to_uri)
        elif to_uri and os.path.exists(to_uri):
            if os.path.exists("%s.s3db" % to_uri):
                if self.use_db:
                    self.add_continue(to_uri)
                else:
                    os.remove("%s.s3db" % to_uri)
                    self.add_new_file(from_uri, to_uri)
            else:
                self.add_new_file(from_uri, to_uri)
        else:
            self.add_new_file(from_uri, to_uri)
        if not self._threads:
            self._start_transfer_thread(self._max_threads)

    def add_new_file(self, from_uri, to_uri=None):
        new_file = FileTransfer(self)
        new_file.set_uri(from_uri, to_uri)
        if self.running == 0:
            self._start_time = datetime.datetime.now()
            self._count_bytes = 0
        self._files[str(id(new_file))] = new_file
        try:
            new_file.start()
        except TransferFailedError:
            pass
        return new_file

    def add_continue(self, file_path):
        if os.path.exists(file_path):
            new_file = FileTransfer(self)
            new_file.set_continue(file_path)
            if self.running == 0:
                self._start_time = datetime.datetime.now()
                self._count_bytes = 0
            self._files[str(id(new_file))] = new_file
            try:
                new_file.start()
            except TransferFailedError:
                pass
        else:
            raise Exception("文件%s不存在" % file_path)

    def wait(self):
        self._end = True
        while True:
            all_end = True
            for thread in self._threads:
                if thread.is_alive():
                    all_end = False
                else:
                    thread.join()
            if all_end:
                break
            for key, f in self._files.items():
                if f.finish:
                    self._files.pop(key)
            gevent.sleep(1)
        failed_files = []
        for f in self._files.values():
            if not f.finish:
                failed_files.append(f.from_path)
        if len(failed_files) > 0:
            raise Exception("文件传输失败: %s" % failed_files)

    def _start_transfer_thread(self, number):
        for i in xrange(number):
            thread = Thread(target=self._download_, args=(), name="download thread %s" % i)
            thread.start()
            self._threads.append(thread)

    def _download_(self):
        while True:
            if self.file_queue.empty():
                if self._end:
                    break
                elif not self.main_thread.is_alive():
                    break
            else:
                try:
                    data = self.file_queue.get()
                    if data:
                        file_transfer = self._files[str(data[0])]
                        if file_transfer.type == 0:
                            thread = S3DownloadThread(file_transfer, data[1])
                        else:
                            thread = S3UploadThread(file_transfer, data[1])
                        thread.start()
                except Exception:
                    exstr = traceback.format_exc()
                    print exstr
                    sys.stdout.flush()


class FileTransfer(object):
    def __init__(self, manager):
        self.manager = manager
        self._config = self.manager.config
        self.min_size_to_split = self._config.get_rgw_min_size_to_split()
        self._chunk_size = 0
        self._conn = None
        self._type = 0
        self._from_uri = None
        self._to_uri = None
        self._region = None
        self._bucket = None
        self._key = None
        self._size = 0
        self._key_obj = None
        self._bucket_obj = None
        self._total_chunk = 0
        self._finish_chunk = 0
        self._is_start = False
        self._continue_mode = False
        self._multi_upload = None
        self._end_threads = 0
        self._db = None
        self._continue_file = None
        self._finished_chunks = []
        self._upload_id = None
        self._finished_size = 0
        self.lock = Lock()
        self._multi_lock = Lock()

    def end_chunk(self, index, length, success=True):
        with self.lock:
            if self.manager.use_db and self.chunks > 1:
                try:
                    if not os.path.exists(self.db_file):
                        db = TransferDB(self)
                        db.save_info()
                        db.close()
                except:
                    pass
            self._end_threads += 1
            if success:
                self.manager.update(length)
                self._finish_chunk += 1
                self._finished_size += length
                if self.chunks > 1 and self.manager.use_db:
                    try:
                        db = TransferDB(self)
                        db.finish_chunk(index)
                        db.close()
                    except:
                        pass
                if self.manager.log:
                    if self._type == 0:
                        print "Downloading %s to %s, Size (%s/%s), Speed %s.." % \
                              (self.from_path, self.to_path, friendly_size(self._finished_size),
                               friendly_size(self.size), self.manager.speed)
                    else:
                        print "Uploading %s to %s, Size (%s/%s), Speed %s.." % \
                              (self.from_path, self.to_path, friendly_size(self._finished_size),
                               friendly_size(self.size), self.manager.speed)
                    sys.stdout.flush()

            if self.manager.callback is not None:
                self.manager.callback(self)

            if self.finish:
                print "File %s trans success!" % self.from_path
                if self._type == 1 and self.chunks > 1:
                    if self.multi_upload:
                        self.multi_upload.complete_upload()
                if self.manager.etag:
                    if self.chunks > 1:
                        if self.key_file:
                            self.key_file.close(fast=True)
                        key = self.bucket.get_key(self._key)
                    else:
                        key = self.key_file
                    if key and key.etag:
                        xattr.setxattr(self.local_file, "user.etag", key.etag.strip('"'))
                    if key:
                        key.close(fast=True)
                if os.path.exists(self.db_file):
                    try:
                        os.remove(self.db_file)
                    except:
                        pass
            else:
                if self.is_end and not self.manager.use_db and self._type == 1 and self.chunks > 1:
                    self.cancel()

    @property
    def chunk_size(self):
        if self._type == 0:
            self._chunk_size = self._config.get_rgw_download_chunk_size()
        else:
            self._chunk_size = self._config.get_rgw_upload_chunk_size()
        return self._chunk_size

    @property
    def type(self):
        return self._type

    def set_uri(self, from_uri, to_uri):
        m = re.match(r"^([\w+\-]+)://([\w+\-]+)/(.*)$", from_uri)
        if m:
            self._type = 0
            self._region = m.group(1)
            self._bucket = m.group(2)
            self._key = m.group(3)
            self._from_uri = from_uri
            if to_uri is None:
                to_uri = os.path.join(self.manager.base_path, self._bucket, self._key)
                if os.path.exists(to_uri):
                    os.remove(to_uri)
            self._to_uri = os.path.abspath(to_uri)
            dir_name = os.path.dirname(self._to_uri)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
        else:
            if not to_uri:
                raise Exception("上传模式必须设置上传路径!")
            m = re.match(r"^([\w+\-]+)://([\w+\-]+)/(.*)$", to_uri)
            if m:
                self._type = 1
                if os.path.isdir(from_uri):
                    raise Exception("不能上传文件夹: %s " % from_uri)
                elif os.path.islink(from_uri):
                    self._from_uri = os.path.abspath(os.path.realpath(from_uri))
                else:
                    self._from_uri = os.path.abspath(from_uri)
                self._region = m.group(1)
                self._bucket = m.group(2)
                self._key = m.group(3)
                self._to_uri = to_uri
            else:
                raise Exception("请设置正确的RGW路径,from:%s, to:%s" % (from_uri, to_uri))
        if not self.exists():
            raise Exception("源文件%s不存在，不能上传或下载!" % self._from_uri)

    def target_exits(self):
        if self._type == 0:
            if os.path.exists(self.to_path):
                return True
            else:
                return False
        else:
            key = self.bucket.get_key(self._key)
            if key:
                key.close(fast=True)
                return True
            else:
                return False

    def remove_target(self):
        if self._type == 0:
            if os.path.exists(self.to_path):
                os.remove(self.to_path)
        else:
            key = self.bucket.get_key(self._key)
            if key:
                key.delete()
                key.close(fast=True)

    @property
    def is_continue(self):
        return self._continue_mode

    @property
    def from_path(self):
        return self._from_uri

    @property
    def to_path(self):
        return self._to_uri

    @property
    def local_file(self):
        if self.is_continue:
            return self._continue_file
        if self._type == 0:
            return self._to_uri
        else:
            return self._from_uri

    @property
    def db_file(self):
        return "%s.s3db" % self.local_file

    @property
    def key_file(self):
        if not self._key_obj:
            if self._type == 0:
                self._key_obj = self.bucket.get_key(self._key)
            else:
                self._key_obj = Key(bucket=self.bucket, name=self._key)
        return self._key_obj

    def exists(self):
        if self._type == 0:
            if self.key_file:
                self.key_file.close(fast=True)
                return True
        else:
            if os.path.exists(self._from_uri):
                return True
        return False

    @property
    def bucket(self):
        if not self._bucket_obj:
            self._bucket_obj = Bucket(connection=self.conn, name=self._bucket)
        return self._bucket_obj

    @property
    def bucket_name(self):
        return self._bucket

    @property
    def key_name(self):
        return self._key

    @property
    def type(self):
        return self._type

    @property
    def size(self):
        if self._type == 0:
            resp = self.conn.make_request("HEAD", self._bucket, self._key)
            if resp.status == 200 and resp.getheader("content-length") and resp.getheader("content-length") != "":
                self._size = int(resp.getheader("content-length"))
            else:
                self._size = self.key_file.size
            resp.close()
        else:
            self._size = os.path.getsize(self._from_uri)
        return self._size

    @property
    def finish_size(self):
        return self.finish_chunks * self.chunk_size

    @property
    def conn(self):
        if not self._conn:
            self._conn = self._config.get_conn_from_bcl(self._region, self._bucket, self.manager.bcl_type)
        return self._conn

    @property
    def chunks(self):
        if self.chunk_size == 0 or self.min_size_to_split == 0:
            self._total_chunk = 1
        if self._total_chunk == 0:
            if self.size >= self.min_size_to_split:
                self._total_chunk = int(math.ceil(self.size*1.0/self.chunk_size))
            else:
                self._total_chunk = 1
        return self._total_chunk

    def chunk_offset(self, index):
        x = self.chunk_size*index
        return x

    def chunk_len(self, index):
        if self.chunks == 1:
            return self.size
        if index >= self.chunks - 1:
            length = min(self.chunk_size, self.size - self.chunk_offset(index))
            return length
        else:
            return self.chunk_size

    @property
    def finish_chunks(self):
        return self._finish_chunk

    @property
    def finish(self):
        if self.chunks == self.finish_chunks:
            return True
        else:
            return False

    @property
    def is_end(self):
        if self.chunks == self._end_threads:
            return True
        else:
            return False

    @property
    def is_start(self):
        return self._is_start

    @property
    def upload_id(self):
        if self._upload_id is None and self._type == 1 and self.multi_upload:
            self._upload_id = self.multi_upload.id
        else:
            self._upload_id = ""
        return self._upload_id

    @property
    def multi_upload(self):
        with self._multi_lock:
            if not self._multi_upload and self._type == 1 and self.chunks > 1:
                key_uploader = self.bucket.get_all_multipart_uploads(prefix=self.key_name)
                if key_uploader:
                    for k in key_uploader:
                        if self.manager.overwrite:
                            if k.get_all_parts() is not None:
                                k.cancel_upload()
                        else:
                            raise Exception("发现未完成的multi_upload %s, 可能有其他进程在同时传输此文件!" % k.name)
                self._multi_upload = self.bucket.initiate_multipart_upload(self.key_name)
        return self._multi_upload

    def start(self):
        if self.target_exits():
            if not self.is_continue:
                if self.manager.overwrite:
                    self.remove_target()
                else:
                    raise Exception("目标路径%s已经存在，不能上传或下载!" % self.to_path)
        self._is_start = True
        if self._type == 0:
            dir_name = os.path.dirname(self._to_uri)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            if not os.path.exists(self._to_uri):
                with open(self._to_uri, "w"):
                    pass
        for i in xrange(self.chunks):
            if self.is_continue and i in self._finished_chunks:
                continue
            else:
                self.manager.file_queue.put((str(id(self)), i))

    def cancel(self):
        if self.multi_upload:
            self.multi_upload.cancel_upload()

    def set_continue(self, file_path):
        self._continue_mode = True
        self._continue_file = os.path.abspath(file_path)
        if not os.path.exists(self.db_file):
            raise Exception("数据库文件不存在，不能断点续传!")
        db = TransferDB(self)
        data = db.load_info()
        if data:
            self.set_uri(data["from_uri"], data["to_uri"])
            if self._type == 0:
                self._to_uri = self._continue_file
            else:
                self._from_uri = self._continue_file
            if self.size != data["size"]:
                self._continue_mode = False
                self.set_uri(data["from_uri"], data["to_uri"])
            else:
                if self._type == 1:
                    with self._multi_lock:
                        key_uploader = self.bucket.get_all_multipart_uploads(prefix=self.key_name)
                        for k in key_uploader:
                            if k.get_all_parts() is not None:
                                if k.id == data["upload_id"]:
                                    self._multi_upload = k
                                else:
                                    k.cancel_upload()
                    if not self._multi_upload:
                        self._continue_mode = False
                        self.set_uri(data["from_uri"], data["to_uri"])
                        return
                self._chunk_size = data["chunk_size"]
                self._total_chunk = data["chunks"]
                self._finish_chunk += len(data["chunk_list"])
                self._end_threads += len(data["chunk_list"])
                self._finished_chunks = data["chunk_list"]
                for i in self._finished_chunks:
                    self._finished_size += self.chunk_len(i)
                self._upload_id = data["upload_id"]

        else:
            raise Exception("数据库文件%s损坏，无法继续下载!" % self.db_file)
        db.close()


class S3DownloadThread(object):
    def __init__(self, file_transfer, index=0):
        self._file_transfer = file_transfer
        self._index = index
        # print self._len
        self._try_times = 0
        self._finish = False

    @property
    def offset(self):
        return self._file_transfer.chunk_offset(self._index)

    @property
    def len(self):
        return self._file_transfer.chunk_len(self._index)

    @property
    def index(self):
        return self._index

    def _download_part(self):
        offset = self.offset
        data_len = self.len
        try:
            resp = self._file_transfer.conn.make_request("GET", self._file_transfer.bucket_name,
                                                         self._file_transfer.key_name,
                                                         headers={"Range": "bytes=%d-%d" %
                                                                           (offset, offset + data_len - 1)})
        except Exception, e:
            raise TransferError(e)
        else:
            if resp.status == 206 and resp.getheader("content-length") and \
                            int(resp.getheader("content-length")) >= data_len:
                data = resp.read(data_len)
                f = FileChunkIO(self._file_transfer.local_file, 'r+', offset=offset, bytes=data_len)
                f.write(data)
                f.close()
                self._finish = True
                resp.close()
            else:
                resp.close()
                print ("下载文件%s chunk %s 出现错误，准备重新下载，错误信息: %s %s \n %s" %
                                                         (self._file_transfer.from_path, self.index, resp.status,
                                                          resp.reason, resp.msg))
                return self._download_part()

    def _download_all(self):
        try:
            self._file_transfer.key_file.get_contents_to_filename(self._file_transfer.local_file)
        except Exception, e:
            raise TransferError(e)
        else:
            self._finish = True

    def _download(self):
        if self._file_transfer.chunks > 1:
            self._download_part()
        else:
            self._download_all()

    @property
    def finish(self):
        return self._finish

    def download(self):
        # dir_name = os.path.dirname(self._file_transfer.local_file)
        # if not os.path.exists(dir_name):
        #     os.makedirs(dir_name)
        # if not os.path.exists(self._file_transfer.local_file):
        #     with open(self._file_transfer.local_file, "w"):
        #         pass
        if self._try_times > 3:
            raise Exception("File:%s, Index: %s, 下载超过3次未成功，下载失败!" %
                            (self._file_transfer.from_path, self._index))
        try:
            self._try_times += 1
            self._download()

        except TransferError, e:
            exstr = traceback.format_exc()
            print exstr
            print "发生错误:%s，开始重试..." % e
            sys.stdout.flush()
            self.download()
        except Exception, e:
            exstr = traceback.format_exc()
            print exstr
            print "发生错误:%s..." % e
            sys.stdout.flush()
        else:
            return True

    def start(self):
        try:
            self.download()
        except Exception, e:
            exstr = traceback.format_exc()
            print exstr
            print "发生错误:%s，终止数据%s块下载..." % (e, self.index)
            sys.stdout.flush()
        self._file_transfer.end_chunk(self._index, self.len, self._finish)


class S3UploadThread(object):
    def __init__(self, file_transfer, index=0):
        self._file_transfer = file_transfer
        self._index = index
        self._offset = self._file_transfer.chunk_offset(self._index)
        self._len = self._file_transfer.chunk_len(self._index)
        self._try_times = 0
        self._finish = False

    @property
    def offset(self):
        return self._file_transfer.chunk_offset(self._index)

    @property
    def len(self):
        return self._file_transfer.chunk_len(self._index)

    @property
    def index(self):
        return self._index

    def _upload_part(self):
        f = FileChunkIO(self._file_transfer.local_file, 'r', offset=self._offset, bytes=self._len)
        try:
            self._file_transfer.multi_upload.upload_part_from_file(f, self._index + 1)
        except Exception, e:
            raise TransferError(e)
        else:
            f.close()
            self._finish = True

    def _upload_all(self):
        try:
            self._file_transfer.key_file.set_contents_from_filename(self._file_transfer.local_file)
        except Exception, e:
            raise TransferError(e)
        else:
            self._finish = True

    def _upload(self):
        if self._file_transfer.chunks > 1:
            self._upload_part()
        else:
            self._upload_all()

    def upload(self):
        if self._try_times > 3:
            raise Exception("File:%s, Index: %s, 上传超过3次未成功，上传失败!" %
                            (self._file_transfer.from_path, self._index))
        try:
            self._try_times += 1
            self._upload()
        except TransferError, e:
            exstr = traceback.format_exc()
            print exstr
            print "发生错误:%s，开始重试..." % e
            sys.stdout.flush()
            return self.upload()
        except Exception, e:
            exstr = traceback.format_exc()
            print exstr
            print "发生错误:%s，..." % e
            sys.stdout.flush()
        else:
            return True

    @property
    def finish(self):
        return self._finish

    def start(self):
        try:
            self.upload()
        except Exception, e:
            exstr = traceback.format_exc()
            print exstr
            print "发生错误:%s，终止数据%s块上传..." % (e, self.index)
            sys.stdout.flush()
        self._file_transfer.end_chunk(self._index, self.len, self._finish)


class TransferDB(object):
    def __init__(self, file_transfer):
        self._conn = None
        self._file_transfer = file_transfer
        self._db_path = file_transfer.db_file

    @property
    def conn(self):
        if not self._conn:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.text_factory = str
        return self._conn

    @property
    def cursor(self):
        return self.conn.cursor()

    def save_info(self):
        sql = '''
        CREATE TABLE main (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            type       INTEGER,
            name       VARCHAR,
            size       BIGINT,
            chunk_size INTEGER,
            chunks     INTEGER,
            from_uri   VARCHAR,
            to_uri     VARCHAR,
            upload_id  VARCHAR,
            finish     BOOLEAN DEFAULT (0)
        );
        '''
        self.cursor.execute(sql)
        sql = '''
            CREATE TABLE chunks (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                number  INTEGER,
                off_set BIGINT,
                len     INTEGER,
                finish  BOOLEAN DEFAULT (0)
            );
            '''
        self.cursor.execute(sql)
        sql = "insert into main (type,name,size,chunk_size,chunks,from_uri,to_uri,upload_id) VALUES(?,?,?,?,?,?,?,?)"
        self.cursor.execute(sql, (self._file_transfer.type, os.path.basename(self._file_transfer.local_file),
                            self._file_transfer.size, self._file_transfer.chunk_size, self._file_transfer.chunks,
                            self._file_transfer.from_path, self._file_transfer.to_path, self._file_transfer.upload_id))
        # sql = "insert into chunks (number,off_set,len) VALUES (?,?,?)"
        # data = []
        # for i in xrange(self._file_transfer.chunks):
        #     data.append((i, self._file_transfer.chunk_offset(i), self._file_transfer.chunk_len(i)))
        # self.cursor.executemany(sql, data)
        self.conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
        self._conn = None

    def load_info(self):
        info = {}
        sql = "select type,name,size,chunk_size,chunks,from_uri,to_uri,finish,upload_id from main"
        result = self.cursor.execute(sql)
        if result:
            row = result.fetchone()
            if row:
                info["type"] = row[0]
                info["size"] = row[2]
                info["chunk_size"] = row[3]
                info["chunks"] = row[4]
                info["from_uri"] = row[5]
                info["to_uri"] = row[6]
                info["finish"] = row[7]
                info["upload_id"] = row[8]
            else:
                return None
        sql = "select number,off_set,len from chunks where finish=1"
        result = self.cursor.execute(sql)
        chunks = []
        if result:
            for row in result:
                    chunks.append(row[0])
        info["chunk_list"] = chunks
        return info

    def finish_chunk(self, index):
        sql = "insert into chunks (number,off_set,len,finish) VALUES (?,?,?,?)"
        self.cursor.execute(sql, (index, self._file_transfer.chunk_offset(index),
                                  self._file_transfer.chunk_len(index), 1))
        self.conn.commit()

    def finish(self):
        sql = "update main set finish =1"
        self.cursor.execute(sql)
        self.conn.commit()
