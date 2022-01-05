
from .app import App

from pathlib import Path

import urllib.request


def download_progress_tar(app: App, url: str, dest: Path, description: str="Downloading file...", *, modify_entry=None):
    """
    Download and directly extract a tar archive
    :param app: The global app instance
    :param url: The url to download
    :param dest: Path to extract into
    :param description: Description text for the progress dialog
    :param modify_entry: May be a function (entry: TarInfo)->None to modify archive entries before extracting
    """
    with a.show_progress(f"{description}\n\nConnecting") as p:
        try:
            with urllib.request.urlopen(url) as f:
                f: urllib.response.addinfourl
                maxi = p.maximum = int(f.info().get("content-length", 0))
                with tarfile.open(mode="r|*", fileobj=f, encoding="utf-8") as tar:
                    tar: tarfile.TarFile
                    dest.mkdir()
                    while info := tar.next():
                        info: tarfile.TarInfo
                        if modify_entry is not None:
                            modify_entry(info)
                        p.text = f"{progress_header}\n\nExtracting '{info.name}'"
                        # Make sure we never go over 100%
                        if info.offset >= maxi:
                            p.maximum = info.offset + 1
                        p.progress = info.offset
                        # Actually do the work
                        tar.extract(info, dest)
        except urllib.request.URLError as e:
            r.show_error(f"Could not connect to '{url}':\n{e.reason}")
            raise
        except:
            import traceback
            r.show_error(f"Error downloading from '{url}':\n\n{traceback.format_exc()}")
            shutil.rmtree(nwjs.get_path("dist"), ignore_errors=True)
            raise