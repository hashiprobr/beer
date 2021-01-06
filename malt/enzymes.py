import tarfile

from io import BytesIO
from tarfile import TarError
from zipfile import BadZipFile, ZipFile

from django.conf import settings


class EnzymeError(Exception):
    pass


class Enzyme:
    def convert(self, content):
        file = BytesIO(content)

        try:
            archive = self.open(file)
        except self.Error:
            raise EnzymeError('could not open')

        try:
            infos = [info for info in self.infos(archive) if self.is_file(info)]

            size = sum(self.size(info) for info in infos)
            if size > settings.FILE_UPLOAD_MAX_TEMPORARY_SIZE:
                raise EnzymeError('cannot have more than 25MB uncompressed')

            return [(self.date(info), self.path(info), self.read(archive, info)) for info in infos]
        finally:
            self.close(archive)


class ZipEnzyme(Enzyme):
    extension = 'zip'
    Error = BadZipFile

    def open(self, file):
        return ZipFile(file)

    def infos(self, archive):
        return archive.infolist()

    def is_file(self, info):
        return not info.is_dir()

    def size(self, info):
        return info.file_size

    def date(self, info):
        return None

    def path(self, info):
        return info.filename

    def read(self, archive, info):
        return archive.read(info.filename)

    def close(self, archive):
        archive.close()


class TarEnzyme(Enzyme):
    extension = 'tar'
    Error = TarError

    def open(self, file):
        return tarfile.open(fileobj=file)

    def infos(self, archive):
        return archive.getmembers()

    def is_file(self, info):
        return info.isfile()

    def size(self, info):
        return info.size

    def date(self, info):
        return info.mtime

    def path(self, info):
        return info.name

    def read(self, archive, info):
        return archive.extractfile(info).read()

    def close(self, archive):
        archive.close()
