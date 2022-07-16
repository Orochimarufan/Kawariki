from pathlib import Path
from shutil import rmtree
from tarfile import TarFile, TarInfo
from tarfile import open as taropen
from typing import Callable, Optional
from urllib.error import URLError
from urllib.request import urlopen

from .app import App
from .distribution import Distribution


def download_progress_tar(app: App, url: str, dest: Path, description: str="Downloading file...",
        *, modify_entry: Optional[Callable]=None):
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
                    dest.mkdir(parents=True)
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


def download_dist_progress_tar(app: App, dist: Distribution):
    strip_prefix: Optional[Callable]
    if dist.strip_leading is True:
        def strip_prefix(entry):
            try:
                index = entry.name.index("/")
            except ValueError:
                # Skip files in archive root
                return False
            entry.name = entry.name[index+1:]
    elif dist.strip_leading is not False:
        def strip_prefix(entry):
            # Figure out filename, strip prefix
            # there isn't really a good way of figuring out a common prefix in stream mode
            # so just strip the leading path component if it starts with a known prefix for now
            if '/' in entry.name:
                dir, name = entry.name.split("/", 1)
                if dir.startswith(dist.strip_leading):
                    entry.name = name
    else:
        strip_prefix = None

    download_progress_tar(app, dist.url, dist.path,
        description=f"Downloading distribution '{dist.name}'",
        modify_entry=strip_prefix)
