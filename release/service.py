from typing import List


class Service:
    def __init__(
        self,
        image_name: str,
        related_files: List[str],
        latest_tag: str,
        prev_tag: str,
        pushed_date: str,
    ):
        self.release_notes = None
        self.image_name = image_name
        self.related_files = related_files
        self.latest_tag = latest_tag
        self.prev_tag = prev_tag
        self.pushed_date = pushed_date

    def add_file(self, file: str):
        self.related_files.append(file)

    def set_release_notes(self, notes: str):
        self.release_notes = notes

    def set_latest_tag(self, latest_tag: str):
        self.latest_tag = latest_tag

    def set_pushed_date(self, date: str):
        self.pushed_date = date
