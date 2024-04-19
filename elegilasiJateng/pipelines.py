from scrapy.pipelines.files import FilesPipeline

import os 

class CustomFilesPipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        if item is not None:
            return super().get_media_requests(item, info)
        else:
            return []

    def file_path(self, request, response=None, info=None, *, item=None):
        if item is not None:
            sub_menu = item.get('sub_menu')

            if not sub_menu:
                sub_menu = 'unsorted'

            nama_file = item.get('filename', '')
            path_file = 'files'
            path = os.path.join(path_file, nama_file)
            return path
