
from pathlib import Path
from shutil import rmtree
from tarfile import TarFile, TarInfo
from tarfile import open as taropen
from urllib.error import URLError
from urllib.request import urlopen

from .app import App


def download_progress_tar(app: App, url: str, dest: Path, description: str="Downloading file...", *, modify_entry=None):
    """
    Download and directly extract a tar archive
    :param app: The global app instance
    :param url: The url to download
    :param dest: Path to extract into
    :param description: Description text for the progress dialog
    :param modify_entry: May be a function (entry: TarInfo)->None to modify archive entries before extracting
    """
    with app.show_progress(f"{description}\n\nConnecting") as p:
        try:
            with urlopen(url) as f:
                maxi = p.maximum = int(f.info().get("content-length", 0))
                with taropen(mode="r|*", fileobj=f, encoding="utf-8") as tar:
                    dest.mkdir()
                    while info := tar.next():
                        if modify_entry is not None:
                            if modify_entry(info) is False:
                                continue
                        p.text = f"{description}\n\nExtracting '{info.name}'"
                        # Make sure we never go over 100%
                        if info.offset >= maxi:
                            p.maximum = info.offset + 1
                        p.progress = info.offset
                        # Actually do the work
                        tar.extract(info, dest)
        except URLError as e:
            app.show_error(f"Could not connect to '{url}':\n{e.reason}")
            raise
        except:
            import traceback
            app.show_error(f"Error downloading from '{url}':\n\n{traceback.format_exc()}")
            rmtree(dest, ignore_errors=True)
            raise
