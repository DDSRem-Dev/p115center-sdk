__all__ = ["P115Center"]
__version__ = "0.0.12"


from base64 import b64decode
from gzip import compress, decompress
from time import sleep
from typing import Optional, Any, Dict, Tuple, List, Literal, Union
from os.path import getsize as path_getsize

from httpx import Client, Response, RequestError
from orjson import dumps, loads

from .schemas.mediainfo_data import UploadMediaInfoData
from .schemas.offline import OfflineInfo, OfflineInfoRes
from .schemas.share import ShareInfo, ShareInfoRes, ShareIterUploadInfo
from .schemas.speed import UserSpeedStatus
from .schemas.upload import UploadInfo, UploadInfoRes
from .sign import Sign


class Requester:
    """
    请求器
    """

    def __init__(self, max_retries: int = 3, backoff_factor: float = 0.5):
        """
        初始化请求类

        :param max_retries: 最大重试次数
        :param backoff_factor: 重试间隔时间因子
        """
        self.encrypted_base_url = "DkIVPxRiQUVHYXI+Cjo4EQFXVykmHT8cCzQJGw=="
        self.encryption_key = (
            "f6aOgXnjvPGMoHNtsy3MUoZq%WfvBFspc3QXOwxy4bhJST@*Hno6r^Qe5JusRbpC"
        )
        self.base_url = self._decrypt_string(
            self.encrypted_base_url, self.encryption_key
        )

        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = Client(follow_redirects=True)

        self.session.headers.update(
            {
                "User-Agent": f"P115Center-SDK/({__version__})",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
        )

    @staticmethod
    def _decrypt_string(encoded_string: str, key: str) -> str:
        """
        对Base64编码的加密字符串进行解密
        """
        try:
            encrypted_bytes = b64decode(encoded_string.encode("utf-8"))
            encrypted_text = encrypted_bytes.decode("utf-8")

            decrypted_chars = []
            for i, char in enumerate(encrypted_text):
                key_char = key[i % len(key)]
                decrypted_char = ord(char) ^ ord(key_char)
                decrypted_chars.append(chr(decrypted_char))

            return "".join(decrypted_chars)
        except (ValueError, TypeError) as e:
            raise RuntimeError(f"解密服务器地址失败: {e}") from e

    def make_request(
        self,
        path: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        files_data: Optional[List[Tuple[str, Tuple[str, bytes, str]]]] = None,
        content_data: Optional[bytes] = None,
        timeout: float = 10.0,
    ) -> Optional[Response]:
        """
        执行安全请求

        :param path: 请求Path
        :param method: HTTP方法 (GET, POST等)
        :param headers: 请求头
        :param json_data: JSON请求体
        :param files_data: 文件上传数据。格式为 httpx 的 files 参数格式，例如:
                         [('files', ('filename1.txt', b'content1', 'text/plain')),
                          ('files', ('filename2.jpg', b'content2', 'image/jpeg'))]
        :param content_data: 内容数据
        :param timeout: 超时时间(秒)
        :return: 响应对象或None
        """
        final_headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        if headers:
            final_headers.update(headers)

        kwargs = {"headers": final_headers, "timeout": timeout}
        if json_data and method.upper() in ["POST", "PUT", "PATCH"]:
            final_headers["accept"] = "application/json"
            final_headers["Content-Type"] = "application/json"
            kwargs["json"] = json_data
        elif files_data and method.upper() == "POST":
            kwargs["files"] = files_data  # noqa
            final_headers.pop("Content-Type", None)
        elif content_data:
            kwargs["content"] = content_data  # noqa

        last_exception = None

        full_url = self.base_url + path

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, full_url, **kwargs)

                response.raise_for_status()

                return response

            except RequestError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    sleep_time = self.backoff_factor * (2**attempt)
                    sleep(sleep_time)

        if last_exception:
            raise last_exception
        return None


class P115Center:
    """
    请求模块
    """

    def __init__(self, machine_id: str = "", license: str = "", file_path: str = ""):
        """
        初始化请求模块

        :param machine_id: 机器ID（可选）
        :param license: 授权码（可选）
        :param file_path: 校验文件路径（可选）
        """
        self.session = Requester(max_retries=3, backoff_factor=1.0)
        self.machine_id = machine_id
        self.headers = {"x-machine-id": self.machine_id}
        self.sign = Sign(
            license,
            file_path,
        )

    def user_speed_status(self) -> Optional[UserSpeedStatus]:
        """
        获取当前用户的速度状态

        :return: UserSpeedStatus
        """
        resp = self.session.make_request(
            path="/speed/user_status/me",
            method="GET",
            headers=self.headers,
            timeout=10.0,
        )
        return UserSpeedStatus(**resp.json())

    def upload_info(self, payload: UploadInfo) -> UploadInfoRes:
        """
        上传上传信息

        :param payload: UploadInfo
        :return: UploadInfoRes
        """
        resp = self.session.make_request(
            path="/upload/info",
            method="POST",
            headers=self.headers,
            json_data=payload.model_dump(mode="json"),
            timeout=10.0,
        )
        return UploadInfoRes(**resp.json())

    def get_upload_info(self) -> List[UploadInfoRes]:
        """
        获取当前用户的所有上传记录

        :return: List[UploadInfoRes]
        """
        resp = self.session.make_request(
            path="/upload/info_all",
            method="GET",
            headers=self.headers,
            timeout=10.0,
        )
        return [UploadInfoRes(**i) for i in resp.json()]

    def upload_wait(self) -> None:
        """
        为当前用户增加一次上传等待计数
        """
        self.session.make_request(
            path="/upload/wait",
            method="POST",
            headers=self.headers,
            timeout=10.0,
        )

    def upload_share_info(
        self, mtype: Literal["115", "ali"], payload: ShareInfo
    ) -> ShareInfoRes:
        """
        上传 115/aliyunpan 分享信息

        :param mtype: 上传类型：115、ali
        :param payload: ShareInfo
        :return: ShareInfoRes
        """
        resp = self.session.make_request(
            path="/share/info" if mtype == "115" else "/ali_share/info",
            method="POST",
            headers=self.headers,
            json_data=payload.model_dump(mode="json"),
            timeout=10.0,
        )
        return ShareInfoRes(**resp.json())

    def upload_offline_info(self, payload: OfflineInfo) -> OfflineInfoRes:
        """
        上传离线下载信息

        :param payload: OfflineInfo
        :return: OfflineInfoRes
        """
        resp = self.session.make_request(
            path="/offline/info",
            method="POST",
            headers=self.headers,
            json_data=payload.model_dump(mode="json"),
            timeout=10.0,
        )
        return OfflineInfoRes(**resp.json())

    def check_feature(self, name: str = "") -> Dict[str, Any]:
        """
        判断是否有权限使用此增强功能

        :param name: 功能名称
        :return: Dict[str, Any]
        """
        resp = self.session.make_request(
            path=f"/machine/feature/{name}",
            method="GET",
            headers=self.headers,
            timeout=10.0,
        )
        return resp.json()

    def get_authorization_status(self) -> Dict[str, Any]:
        """
        获取机器授权状态

        :return: Dict[str, Any]
        """
        resp = self.session.make_request(
            path="/machine/authorization/status",
            method="GET",
            headers=self.headers,
            timeout=10.0,
        )
        return resp.json()

    def download_share_file_iter(self, batch_id: str, temp_file: str) -> None:
        """
        下载分享文件信息迭代数据

        :param batch_id: 上传 Batch Id
        :param temp_file: 临时文件路径
        """
        resp = self.session.make_request(
            path=f"/share/files/{batch_id}",
            method="GET",
            timeout=6000.0,
        )
        with open(temp_file, "wb") as f:
            for chunk in resp.iter_bytes():
                f.write(chunk)

    def upload_share_file_iter(
        self, batch_id: str, temp_file: str
    ) -> ShareIterUploadInfo:
        """
        上传分享文件信息迭代数据

        :param batch_id: 上传 Batch Id
        :param temp_file: 临时文件路径
        :return: ShareIterUploadInfo
        """
        file_name = f"{batch_id}.json.gz"
        file_size = path_getsize(temp_file)
        file_content = bytes()
        if file_size > 100 * 1024 * 1024:
            file_content = bytearray()
            with open(temp_file, "rb") as f:
                while chunk := f.read(8 * 1024 * 1024):
                    file_content.extend(chunk)
            file_content = bytes(file_content)
        else:
            with open(temp_file, "rb") as f:
                file_content = f.read()
        files_data = [
            (
                "file",
                (file_name, file_content, "application/gzip"),
            )
        ]
        resp = self.session.make_request(
            path=f"/share/files/{batch_id}",
            method="POST",
            files_data=files_data,
            timeout=600000.0,
            headers=self.sign.get_sign("POST", f"/share/files/{batch_id}"),
        )
        return ShareIterUploadInfo(**resp.json())

    def upload_mediainfo_data(
        self, payload: List[Tuple[str, Tuple[str, bytes, str]]]
    ) -> UploadMediaInfoData:
        """
        上传 115 网盘的媒体信息数据文件

        :param payload: 媒体信息数据列表
        :return: UploadMediaInfoData
        """
        resp = self.session.make_request(
            method="POST",
            path="/mediainfo_data/bulk",
            files_data=payload,
            timeout=600.0,
            headers=self.sign.get_sign("POST", "/mediainfo_data/bulk"),
        )
        return UploadMediaInfoData(**resp.json())

    def download_mediainfo_data(self, payload: List[str]) -> List[Dict[str, Any]]:
        """
        下载 115 网盘的媒体信息数据文件

        :param payload: 媒体信息数据文件 sha1 列表
        :return: 每项为 {"sha1": str, "data": str | None}，data 为 base64 编码
        """
        resp = self.session.make_request(
            method="POST",
            path="/mediainfo_data/get",
            json_data={"sha1s": payload},
        )
        return resp.json()

    @staticmethod
    def get_emby_media_source_size(media_data: Any) -> Optional[int]:
        """
        从媒体信息中取出 MediaSourceInfo.Size。

        :param media_data: 中心下发的或 Emby 返回的媒体信息
        :return: size 字节数，取不到则返回 None
        """
        if not media_data:
            return None
        item = media_data[0] if isinstance(media_data, list) else media_data
        if not isinstance(item, dict):
            return None
        msi = item.get("MediaSourceInfo")
        if not isinstance(msi, dict):
            return None
        size = msi.get("Size")
        return int(size) if size is not None else None

    @staticmethod
    def _size_mismatch(expected: Optional[int], actual: int) -> bool:
        """
        判断预期大小与实际大小是否超出 0.5% 误差

        :param expected: 预期大小（字节）；为 None 或 ≤0 时不校验，视为通过
        :param actual: 实际大小（字节）
        :return: True 表示不通过（相对误差超过 0.5%），False 表示通过（在容差内或未校验）
        """
        if expected is None or expected <= 0:
            return False
        return abs(actual - expected) > expected * 0.005

    def upload_emby_mediainfo_data(
        self, sha1: str, data: Dict[str, Any], /, size: Optional[int] = None
    ) -> bool:
        """
        上传 Emby 的媒体信息数据

        :param sha1: 媒体信息数据 SHA1
        :param data: 媒体信息数据
        :param size: 媒体信息数据大小(字节)
        :return: 是否上传成功
        """
        actual_size = self.get_emby_media_source_size(data)
        if actual_size is None:
            return False
        if self._size_mismatch(size, actual_size):
            return False
        self.session.make_request(
            method="POST",
            path="/emby_mediainfo_data/upload",
            content_data=compress(dumps(data)),
            headers={
                "Content-Type": "application/x-gzip",
                "X-SHA1": sha1.upper(),
                **self.sign.get_sign("POST", "/emby_mediainfo_data/upload"),
            },
            timeout=600.0,
        )
        return True

    def upload_emby_mediainfo_data_bulk(
        self,
        payload: List[
            Union[
                Tuple[str, Dict[str, Any]],
                Tuple[str, Dict[str, Any], Optional[int]],
            ]
        ],
    ) -> UploadMediaInfoData:
        """
        批量上传 Emby 的媒体信息数据

        :param payload: (sha1, 媒体信息数据) 或 (sha1, 媒体信息数据, size) 列表
        :return: UploadMediaInfoData；校验不通过的项会跳过
        """
        files_data = []
        for item in payload:
            if len(item) == 2:
                sha1, data = item
                size = None
            else:
                sha1, data, size = item
            actual_size = self.get_emby_media_source_size(data)
            if actual_size is None:
                continue
            if self._size_mismatch(size, actual_size):
                continue
            files_data.append(
                ("files", (sha1.upper(), compress(dumps(data)), "application/gzip"))
            )
        if not files_data:
            return UploadMediaInfoData(
                inserted_count=0, modified_count=0, total_processed=0
            )
        resp = self.session.make_request(
            method="POST",
            path="/emby_mediainfo_data/bulk",
            files_data=files_data,
            timeout=600.0,
            headers=self.sign.get_sign("POST", "/emby_mediainfo_data/bulk"),
        )
        return UploadMediaInfoData(**resp.json())

    def download_emby_mediainfo_data(
        self,
        payload: Union[List[str], List[Tuple[str, Optional[int]]]],
    ) -> Dict[str, Optional[Any]]:
        """
        根据 SHA1 列表批量获取 Emby 媒体信息数据

        :param payload: sha1 列表，或 (sha1, size) 列表用于校验；单次最多 2000 条
        :return: 键为 sha1，值为媒体信息数据；无 Size 或 size 校验不通过时为 None
        """
        if payload and isinstance(payload[0], tuple):
            sha1_list = [s.upper() for s, _ in payload]
            size_by_sha1 = {s.upper(): size for s, size in payload}
        else:
            sha1_list = [s.upper() for s in payload]
            size_by_sha1 = {}
        resp = self.session.make_request(
            method="POST",
            path="/emby_mediainfo_data/get",
            json_data={"sha1s": sha1_list},
        )
        items = resp.json()
        result = {}
        for it in items:
            sha1 = it["sha1"].upper()
            raw = it.get("data")
            if raw is None:
                result[sha1] = None
                continue
            data = loads(decompress(b64decode(raw)))
            actual_size = self.get_emby_media_source_size(data)
            if actual_size is None:
                result[sha1] = None
                continue
            expected_size = size_by_sha1.get(sha1)
            if self._size_mismatch(expected_size, actual_size):
                result[sha1] = None
                continue
            result[sha1] = data
        return result
