import asyncio
from functools import wraps
import re
import sys
from typing import Any, Union
from natsort import natsorted
from rich import box
from rich import print as rprint
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from .models import ApiResponseModel, Task, TaskResult


class Debug:
    """
    工具类
    """

    debug_enabled = True
    output_enabled = True

    @staticmethod
    def catch_exceptions_not_stop(func):
        """
        捕获函数异常
        """

        @wraps(func)
        def wrapper(*args, **kwargs) -> TaskResult:
            # 捕获错误
            try:
                return TaskResult(
                    func_name=func.__qualname__,
                    args=list(args, **kwargs),
                    success=True,
                    data=func(*args, **kwargs),
                    error="",
                )

            except Exception as e:
                return TaskResult(
                    func_name=func.__qualname__,
                    args=list(args, **kwargs),
                    success=False,
                    data=ApiResponseModel(
                        success=False, status_code=500, error="", data={}
                    ),
                    error=str(e),
                )

        return wrapper

    @staticmethod
    def stop_on_error(result_list: list[TaskResult]):
        """在错误时停止"""
        for result in result_list:
            if not result.success:
                Message.error("任务执行失败, 退出程序")
                rprint(result)
                sys.exit(0)


class Message:
    """打印消息类"""

    @staticmethod
    def config_input():
        url = Prompt.ask(
            Message.question("请输入Alist地址"), default="http://127.0.0.1:5244"
        )
        user = Prompt.ask(Message.question("请输入账号"))
        password = Prompt.ask(Message.question("请输入登录密码"))
        totp = Prompt.ask(
            Message.question(
                "请输入二次验证密钥(base64加密密钥,非6位数字验证码), 未设置请跳过"
            ),
            default="",
        )
        api_key = Prompt.ask(
            Message.question(
                "请输入TMDB API密钥，用于从TMDB获取剧集/电影信息\t申请链接: https://www.themoviedb.org/settings/api\n"
            )
        )
        return {
            "url": url,
            "user": user,
            "password": password,
            "totp": totp,
            "api_key": api_key,
        }

    @staticmethod
    def success(message: str, printf: bool = True):
        if printf:
            rprint(f":white_check_mark: {message}")
        return f":white_check_mark: {message}"

    @staticmethod
    def error(message: str, printf: bool = True):
        if printf:
            rprint(f":x: {message}")
        return f":x: {message}"

    @staticmethod
    def warning(message: str, printf: bool = True):
        if printf:
            rprint(f":warning:  {message}")
        return f":warning:  {message}"

    @staticmethod
    def ask(message: str, printf: bool = True):
        if printf:
            rprint(f":bell: {message}")
        return f":bell: {message}"

    @staticmethod
    def info(message: str, printf: bool = True):
        if printf:
            rprint(f":information:  {message}")
        return f":information:  {message}"

    @staticmethod
    def congratulation(message: str, printf: bool = True):
        if printf:
            rprint(f":party_popper: {message}")
        return f":party_popper: {message}"

    @staticmethod
    def question(message: str, printf: bool = True):
        if printf:
            rprint(f":abc: {message}")
        return f":abc: {message}"

    @staticmethod
    def text_regex(text: str):
        t = Text(text)
        # t.highlight_regex(r"\d(.*).", "cyan")
        # t.highlight_regex(r"^[^-]+", "blue")
        t.highlight_regex(r"(?<=E)\d+(?=.)", "bright_cyan")
        # t.highlight_regex(r"[^.]+(?=\.\w+$)", "magenta")
        return t

    @staticmethod
    def alist_login_required(func):
        """判断登录状态"""

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 如果未启用调试模式，直接返回结果
            if not Debug.output_enabled:
                return func(self, *args, **kwargs)

            # 判断登录状态
            if self.login_success is False:
                Message.error("操作失败，用户未登录")
                # print(f"{PrintMessage.ColorStr.red('[Alist●Login●Failure]\n')}操作失败，用户未登录")
                # console.print("[blue underline]Looks like a link")
                return {"message": "用户未登录"}
            login_result = func(self, *args, **kwargs)

            return login_result

        return wrapper

    @staticmethod
    def output_alist_login(func):
        """
        输出登录状态信息
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            login_result: ApiResponseModel = func(self, *args, **kwargs)

            # 输出获取Token结果
            if login_result.success:
                Message.success(f"主页: {self.url}")
            else:
                Message.error(f"登录失败\t{login_result.data['message']}")
                sys.exit(0)
            return login_result

        return wrapper

    @staticmethod
    def output_alist_file_list(func):
        """输出文件信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 输出结果
            if not return_data.success:
                Message.error(
                    f"获取文件列表失败: {Tools.get_argument(1, 'path', args, kwargs)}\n   {return_data.data['message']}"
                )
                sys.exit(0)

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_alist_rename(func):
        """输出重命名信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data = func(*args, **kwargs)

            # 输出重命名结果
            # if return_data["message"] != "success":
            #     # print(
            #     #     f"{Message.ColorStr.red('[✗]')} 重命名失败: {Tools.get_argument(2, 'path', args, kwargs).split('/')[-1]} -> {Tools.get_argument(1, 'name', args, kwargs)}\n{return_data['message']}"
            #     # )
            #     Message.error(
            #         f"重命名失败: {Tools.get_argument(2, 'path', args, kwargs).split('/')[-1]} -> {Tools.get_argument(1, 'name', args, kwargs)}\n{return_data['message']}"
            #     )
            # else:
            #     # print(
            #     #     f"{Message.ColorStr.green('[✓]')} 重命名路径:{Tools.get_argument(2, 'path', args, kwargs).split('/')[-1]} -> {Tools.get_argument(1, 'name', args, kwargs)}"
            #     # )
            #     Message.success(
            #         f"重命名路径:{Tools.get_argument(2, 'path', args, kwargs).split('/')[-1]} -> {Tools.get_argument(1, 'name', args, kwargs)}"
            #     )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_alist_move(func):
        """输出文件移动信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 输出移动结果
            if not return_data.success:
                Message.error(
                    f"移动失败: {Tools.get_argument(2, 'src_dir', args, kwargs)} -> {Tools.get_argument(3, 'dst_dir', args, kwargs)}\n   {return_data.data['message']}"
                )
            else:
                Message.success(
                    f"移动路径: {Tools.get_argument(2, 'src_dir', args, kwargs)} -> {Tools.get_argument(3, 'dst_dir', args, kwargs)}"
                )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_alist_mkdir(func):
        """输出新建文件/文件夹信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 输出新建文件夹请求结果
            if not return_data.success:
                Message.error(
                    f"文件夹创建失败: {Tools.get_argument(1, 'path', args, kwargs)}\n   {return_data.data['message']}"
                )
            else:
                Message.success(
                    f"文件夹创建路径: {Tools.get_argument(1, 'path', args, kwargs)}"
                )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_alist_remove(func):
        """输出文件/文件夹删除信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 如果未启用调试模式，直接返回结果
            if not Debug.output_enabled:
                return return_data

            # 输出删除文件/文件夹请求结果
            if not return_data.success:
                Message.error(
                    f"删除失败: {Tools.get_argument(1, 'path', args, kwargs)}\n   {return_data.data['message']}\n{return_data.data['message']}"
                )
            else:
                for name in Tools.get_argument(2, "name", args, kwargs):
                    # print(
                    #     f"{Message.ColorStr.green('[✓]')} 删除路径: {Tools.get_argument(1, 'path', args, kwargs)}/{name}"
                    # )
                    Message.success(
                        f"删除路径: {Tools.get_argument(1, 'path', args, kwargs)}/{name}"
                    )

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_tmdb_tv_info(func):
        """输出剧集信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 请求失败则输出失败信息
            if not return_data.success:
                Message.error(
                    f"tv_id: {Tools.get_argument(1, 'tv_id', args, kwargs)}\n   {return_data.data['status_message']}"
                )
                return return_data

            # 格式化输出请求结果
            first_air_year = return_data.data["first_air_date"][:4]
            name = return_data.data["name"]
            dir_name = f"{name} ({first_air_year})"
            Message.success(dir_name)
            seasons = return_data.data["seasons"]
            table = Table(box=box.SIMPLE)
            table.add_column("开播时间", justify="center", style="cyan")
            table.add_column("集数", justify="center", style="magenta")
            table.add_column("序号", justify="center", style="green")
            table.add_column("剧名", justify="left", no_wrap=True)
            # table.add_column(footer="共计: " + str(len(seasons)), style="grey53")
            for i, season in enumerate(seasons):
                table.add_row(
                    season["air_date"],
                    str(season["episode_count"]),
                    str(i),
                    season["name"],
                )
            rprint(table)

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_tmdb_search_tv(func):
        """输出查找剧集信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 请求失败则输出失败信息
            if not return_data.success:
                Message.error(
                    f"Keyword: {Tools.get_argument(1, 'keyword', args, kwargs)}\n   {return_data.data['status_message']}"
                )
                return return_data
            if not return_data.data["results"]:
                Message.error(
                    f"关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}\n    未查找到相关剧集"
                )
                return return_data

            Message.success(f"关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}")
            table = Table(box=box.SIMPLE)
            table.add_column("开播时间", justify="center", style="cyan")
            table.add_column("序号", justify="center", style="green")
            table.add_column("剧名", justify="left", no_wrap=True)
            # table.add_column(
            #     footer="共计: " + str(len(return_data["results"])), style="grey53"
            # )
            for i, r in enumerate(return_data.data["results"]):
                table.add_row(r["first_air_date"], str(i), r["name"])
            rprint(table)

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_tmdb_tv_season_info(func):
        """输出剧集季度信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 请求失败则输出失败信息
            if not return_data.success:
                Message.error(
                    f"剧集id: {Tools.get_argument(1, 'tv_id', args, kwargs)}\t第 {Tools.get_argument(2, 'season_number', args, kwargs)} 季\n   {return_data.data['status_message']}"
                )
                return return_data

            return return_data

            # # 格式化输出请求结果
            # print(f"{Message.ColorStr.green('[✓]')} {return_data['name']}")
            # print(f"{'序 号':<6}{'放映日期':<12}{'时 长':<10}{'标 题'}")
            # print(f"{'----':<8}{'----------':<16}{'-----':<12}{'----------------'}")

            # for episode in return_data["episodes"]:
            #     print(
            #         f"{episode['episode_number']:<8}{episode['air_date']:<16}{str(episode['runtime']) + 'min':<12}{episode['name']}"
            #     )

            # # 返回请求结果
            # return return_data

        return wrapper

    @staticmethod
    def output_tmdb_movie_info(func):
        """输出电影信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 如果未启用调试模式，直接返回结果
            if not Debug.output_enabled:
                return return_data

            # 请求失败则输出失败信息
            if not return_data.success:
                Message.error(
                    f"tv_id: {Tools.get_argument(1, 'movie_id', args, kwargs)}\n   {return_data.data['status_message']}"
                )
                return return_data

            # 格式化输出请求结果
            Message.success(
                f"{return_data.data['title']} {return_data.data['release_date']}"
            )
            # print(
            #     f"{Message.ColorStr.green('[✓]')} {return_data['title']} {return_data['release_date']}"
            # )

            rprint(f"[标语] {return_data.data['tagline']}")

            rprint(f"[剧集简介] {return_data.data['overview']}")

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def output_tmdb_search_movie(func):
        """输出查找电影信息"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return_data: ApiResponseModel = func(*args, **kwargs)

            # 如果未启用调试模式，直接返回结果
            if not Debug.output_enabled:
                return return_data

            # 请求失败则输出失败信息
            if not return_data.success:
                # print(
                #     f"{Message.ColorStr.red('[✗]')} Keyword: {Tools.get_argument(1, 'keyword', args, kwargs)}\n{return_data['status_message']}"
                # )
                Message.error(
                    f"Keyword: {Tools.get_argument(1, 'keyword', args, kwargs)}\n{return_data.data['status_message']}"
                )
                return return_data

            if not return_data.data["results"]:
                # print(
                #     f"{Message.ColorStr.red('[✗]')} 关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}\n查找不到任何相关电影"
                # )
                Message.error(
                    f"关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}\n查找不到任何相关电影"
                )
                return return_data

            # 格式化输出请求结果
            # print(
            #     f"{Message.ColorStr.green('[✓]')} 关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}"
            # )
            Message.success(f"关键词: {Tools.get_argument(1, 'keyword', args, kwargs)}")
            # print(f"{' 首播时间 ':<8}{'序号':^14}{'电影标题'}")
            # print(f"{'----------':<12}{'-----':^16}{'----------------'}")

            # for i, result in enumerate(return_data["results"]):
            #     if "release_date" in result:
            #         print(f"{result['release_date']:<12}{i:^16}{result['title']}")
            #     else:
            #         print(f"{'xxxx-xx-xx':<12}{i:^16}{result['title']}")

            table = Table(box=box.SIMPLE)
            table.add_column("首播时间", justify="center", style="cyan")
            table.add_column("序号", justify="center", style="green")
            table.add_column("电影标题", justify="left", no_wrap=True)
            # table.add_column(
            #     footer="共计: " + str(len(return_data["results"])), style="grey53"
            # )
            for i, r in enumerate(return_data.data["results"]):
                table.add_row(r["release_date"], str(i), r["title"])
            rprint(table)

            # 返回请求结果
            return return_data

        return wrapper

    @staticmethod
    def print_rename_info(
        video_rename_list: list[dict[str, str]],
        subtitle_rename_list: list[dict[str, str]],
        folder_rename: bool,
        renamed_folder_title: Union[str, None],
        folder_path: str,
    ):
        """打印重命名信息"""
        if len(video_rename_list) > 0:
            Message.info(f"以下视频文件将会重命名: 共计 {len(subtitle_rename_list)}")
            table = Table(box=box.SIMPLE)
            table.add_column("原文件名", justify="left", style="grey53", no_wrap=True)
            table.add_column(" ", justify="left", style="grey70")
            table.add_column("目标文件名", justify="left", no_wrap=True)
            for video in video_rename_list:
                table.add_row(
                    Message.text_regex(video["original_name"]),
                    "->",
                    Message.text_regex(video["target_name"]),
                )
            rprint(table)
        if len(subtitle_rename_list) > 0:
            Message.info(f"以下字幕文件将会重命名: 共计 {len(subtitle_rename_list)}")
            table = Table(box=box.SIMPLE)
            table.add_column("原文件名", justify="left", style="grey53", no_wrap=True)
            table.add_column(" ", justify="left", style="grey70")
            table.add_column("目标文件名", justify="left", no_wrap=True)
            for subtitle in subtitle_rename_list:
                table.add_row(
                    Message.text_regex(subtitle["original_name"]),
                    "->",
                    Message.text_regex(subtitle["target_name"]),
                )
            rprint(table)
        if folder_rename:
            Message.info(
                f"文件夹重命名: [grey53]{folder_path.split('/')[-2]}[/grey53] [grey70]->[/grey70] {renamed_folder_title}"
            )

    @staticmethod
    def require_confirmation() -> bool:
        """确认操作"""

        signal = Confirm.ask(
            Message.warning("确定要重命名吗? ", printf=False), default=True
        )

        if signal:
            return True
        else:
            sys.exit(0)

    @staticmethod
    def select_number(result_list: list[Any]) -> int:
        """根据查询结果选择序号"""
        # 若查找结果只有一项，则无需选择，直接进行下一步
        if len(result_list) == 1:
            return 0
        else:
            while True:
                # 获取到多项匹配结果，手动选择
                number = Prompt.ask(
                    Message.ask(
                        "查询到以上结果，请输入对应[green][序号][/green], 输入[red]\[n][/red]退出",  # type: ignore
                        printf=False,
                    )
                )  # type: ignore
                if number.lower() == "n":
                    sys.exit(0)
                if number.isdigit() and 0 <= int(number) < len(result_list):
                    return int(number)

    @staticmethod
    def print_rename_result(
        tasks: list[TaskResult],
        video_count: int,
        subtitle_count: int,
        folder_count: int,
    ):
        """打印重命名结果"""

        video_error_count = 0
        subtitle_error_count = 0
        folder_error_count = 0
        error_list: list[TaskResult] = []

        # 统计视频重命名结果
        for i in range(video_count):
            if not tasks[i].data.success:
                video_error_count += 1
                error_list.append(tasks[i])

        # 统计字幕重命名结果
        for i in range(video_count, video_count + subtitle_count):
            if not tasks[i].data.success:
                subtitle_error_count += 1
                error_list.append(tasks[i])

        # 统计文件夹重命名结果
        if not tasks[-1].data.success:
            folder_error_count += 1
            error_list.append(tasks[-1])

        # 输出错误信息
        if video_error_count + subtitle_error_count + folder_error_count > 0:
            table = Table(box=box.SIMPLE, title="重命名失败列表")
            table.add_column("原文件名", justify="left", style="grey53")
            table.add_column(" ", justify="left", style="grey70")
            table.add_column("目标文件名", justify="left")
            table.add_column("错误信息", justify="left")
            for result in error_list:
                table.add_row(
                    result.args[1].split("/")[-1],
                    "->",
                    Message.text_regex(result.args[0]),
                    result.data.error,
                )
            rprint(table)

        # 输出重命名结果，成功失败数量
        if video_error_count > 0 and video_count > 0:
            Message.error(
                f"视频文件:  成功 [green]{video_count - video_error_count}[/green], 失败 [red]{video_error_count}[/red]"
            )
        elif video_error_count == 0 and video_count > 0:
            Message.success(f"视频文件: 成功 [green]{video_count}[/green]")
        if subtitle_error_count > 0 and subtitle_count > 0:
            Message.error(
                f"字幕文件: 成功 [green]{subtitle_count - subtitle_error_count}[/green], 失败 [red]{subtitle_error_count}[/red]"
            )
        elif subtitle_error_count == 0 and subtitle_count > 0:
            Message.success(f"字幕文件: 成功 [green]{subtitle_count}[/green]")
        if folder_error_count > 0 and folder_count > 0:
            Message.error(
                f"父文件夹: 成功 [green]{folder_count - folder_error_count}[/green], 失败 [red]{folder_error_count}[/red]"
            )
        elif folder_error_count == 0 and folder_count > 0:
            Message.success(f"父文件夹: 成功 [green]{folder_count}[/green]")

        # 程序运行结束
        rprint("\n")
        Message.congratulation("重命名完成")


class Tools:
    """
    工具函数类
    """

    @staticmethod
    def ensure_slash(path: str) -> str:
        """确保路径以 / 开头并以 / 结尾"""
        if not path.startswith("/"):
            path = "/" + path
        if not path.endswith("/"):
            path = path + "/"
        return path

    @staticmethod
    def get_parent_path(path: str) -> str:
        """获取父目录路径"""
        path = Tools.ensure_slash(path)
        return path[: path[:-1].rfind("/") + 1]

    @staticmethod
    def filter_file(file_list: list, pattern: str) -> list:
        """筛选列表，并以自然排序返回"""

        return natsorted([file for file in file_list if re.match(pattern, file)])

    @staticmethod
    def parse_page_ranges(page_ranges: str, total_pages: int) -> list:
        """
        解析分页格式的字符串，并返回一个包含所有项的列表。

        示例:
        输入: "1,2-4,7,10-13", 11
        输出: [1, 2, 3, 4, 7, 10, 11]

        输入: "3", 13
        输出: [3]

        输入: "3-", 13
        输出: [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

        """
        pages = []
        ranges = page_ranges.split(",")
        for r in ranges:
            if not r:
                continue
            if "-" in r:
                start, end = r.split("-")
                start = int(start)
                end = int(end) if end and int(end) <= total_pages else total_pages
                pages.extend(range(start, end + 1))
            else:
                pages.append(int(r))

        # 去重并排序
        pages = sorted(set(pages))
        return pages

    @staticmethod
    def match_episode_files(
        original_list: list[str],
        target_list: list[str],
        exclude_renamed: bool,
        first_number: str = "1",
    ) -> list[dict[str, str]]:
        """匹配文件"""

        # 创建重命名列表
        rename_list_no_filter: list[dict[str, str]] = []
        # 创建排除已重命名的列表
        rename_list_filter: list[dict[str, str]] = []

        # 创建hash表和队列
        rename_list: list[dict[str, str]] = [{}] * len(target_list)
        target_dict: dict[str, int] = {item: i for i, item in enumerate(target_list)}
        queue = []

        # 优先匹配已重命名的文件
        for i, item in enumerate(original_list):
            if item.rsplit(".", 1)[0] in target_list:
                rename_list[target_dict[item.rsplit(".", 1)[0]]] = {
                    "original_name": item,
                    "target_name": item,
                }
            else:
                queue.append(item)

        # 匹配未重命名的文件
        for i in range(len(target_list)):
            if rename_list[i] != {}:
                rename_list_no_filter.append(rename_list[i])
            if (
                rename_list[i] == {}
                and len(queue) > 0
                and i + 1 in Tools.parse_page_ranges(first_number, len(target_list))
            ):
                original_name: str = queue.pop(0)
                target_name = target_list[i] + "." + original_name.rsplit(".", 1)[1]
                rename_list_no_filter.append(
                    {"original_name": original_name, "target_name": target_name}
                )
                rename_list_filter.append(
                    {"original_name": original_name, "target_name": target_name}
                )

        return rename_list_filter if exclude_renamed else rename_list_no_filter

    @staticmethod
    def get_argument(
        arg_index: int, kwarg_name: str, args: Union[list, tuple], kwargs: dict
    ) -> str:
        """获取参数"""
        if len(args) > arg_index:
            return args[arg_index]
        return kwargs[kwarg_name]

    @staticmethod
    def get_renamed_folder_title(
        tv_info_result, tv_season_info, folder_path, rename_type, tv_season_format
    ) -> str:
        """文件夹重命名类型"""
        if rename_type == 1:
            renamed_folder_title = (
                f"{tv_info_result['name']} ({tv_info_result['first_air_date'][:4]})"
            )
        elif rename_type == 2:
            renamed_folder_title = tv_season_format.format(
                season=tv_season_info["season_number"],
                name=tv_info_result["name"],
                year=tv_info_result["first_air_date"][:4],
            )
        else:
            renamed_folder_title = ""
        return renamed_folder_title

    @staticmethod
    def replace_illegal_char(filename: str, extend=True) -> str:
        """替换非法字符"""
        illegal_char = r"[\/:*?\"<>|]" if extend else r"[/]"
        return re.sub(illegal_char, "_", filename)


class Tasks:
    """多任务运行（异步/同步）"""

    @staticmethod
    def exec_function(func, args):
        """执行函数"""
        decorated_func = Debug.catch_exceptions_not_stop(func)
        return decorated_func(*args)

    @staticmethod
    def run_sync_tasks(task_list: list[Task]) -> list[TaskResult]:
        """同步运行函数集"""

        results = []

        for task in task_list:
            results.append(Tasks.exec_function(task.func, task.args))
        return results

    @staticmethod
    def run_async_tasks(task_list: list[Task]) -> list[TaskResult]:
        """异步运行函数集"""

        async def run_task():
            """异步处理函数"""
            results = []  # 创建一个空字典来存储结果
            futures = []
            for task in task_list:
                future = loop.run_in_executor(
                    None, Tasks.exec_function, task.func, task.args
                )
                futures.append(future)
            for future in futures:
                results.append(await future)
            return results
            # done, pending = await asyncio.wait(futures)
            # 将结果与执行函数对应起来
            # for future in done:
            #     results.append(future.result())
            # return results, pending

        loop = asyncio.new_event_loop()
        done = loop.run_until_complete(run_task())
        loop.close()
        return done

    @staticmethod
    def run(task_list: list[Task], async_mode: bool) -> list[TaskResult]:
        """运行函数集"""
        if async_mode:
            return Tasks.run_async_tasks(task_list)
        return Tasks.run_sync_tasks(task_list)
