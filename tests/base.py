from os import path
from os import remove
from shutil import rmtree
from tempfile import NamedTemporaryFile
from tempfile import mkdtemp


# noinspection PyPep8Naming
class FileWritingTestCaseMixin(object):
    # noinspection PyAttributeOutsideInit
    def setUp(self):
        self.paths_created = set()

    def tearDown(self):
        for created in self.paths_created:
            if path.isdir(created):
                rmtree(created)
            elif path.isfile(created):
                remove(created)

    # noinspection PyUnresolvedReferences
    def assertFileExists(self, filepath):
        self.paths_created.add(filepath)
        self.assertTrue(path.isfile(filepath), 'file does not exist')

    # noinspection PyUnresolvedReferences
    def assertFileDoesNotExist(self, filepath):
        self.paths_created.add(filepath)
        self.assertFalse(path.isfile(filepath), 'file exists')

    # noinspection PyUnresolvedReferences
    def assertDirectoryExists(self, directory):
        self.paths_created.add(directory)
        self.assertTrue(path.isdir(directory), 'directory does not exist')

    # noinspection PyUnresolvedReferences
    def assertDirectoryDoesNotExist(self, directory):
        self.paths_created.add(directory)
        self.assertFalse(path.isdir(directory), 'directory exists')

    # noinspection PyUnresolvedReferences
    def assertFileContentEqual(self, filepath, content):
        self.paths_created.add(filepath)
        self.assertFileExists(filepath)
        with open(filepath) as fobj:
            self.assertEqual(fobj.read(), content, 'file content is different')

    def new_directory(self):
        directory_path = mkdtemp()
        self.paths_created.add(directory_path)
        return directory_path

    def new_file(self, directory=None, content=''):
        directory = directory or self.new_directory()

        with NamedTemporaryFile('w', delete=False, dir=directory) as fobj:
            fobj.write(content)
        self.paths_created.add(fobj.name)
        return fobj.name
