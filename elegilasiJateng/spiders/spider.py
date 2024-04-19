import scrapy
import json
import time
from datetime import datetime
import os
import uuid
import s3fs
import logging

class JatengSpider(scrapy.Spider):
    name = 'jatengspider'
    allowed_domains = ['e-legilasi.jatengprov.go.id']
    start_urls = [
        'https://elegislasi.dprd.jatengprov.go.id/beranda?tahun=2020',
        'https://elegislasi.dprd.jatengprov.go.id/beranda?tahun=2021',
        'https://elegislasi.dprd.jatengprov.go.id/beranda?tahun=2022',
        'https://elegislasi.dprd.jatengprov.go.id/beranda?tahun=2023',
        'https://elegislasi.dprd.jatengprov.go.id/beranda?tahun=2024'
        ]
    
    logger = logging.getLogger(__name__)

    def save_json(self, data, filename):
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=2)

    def clean_name(self, nama):
        return nama.replace(' ', '_').replace(':', '').replace('/', '')

    def data_id_generate(self):
        return int(uuid.uuid4().hex[:4], 16)

    def upload_to_s3(self, local_path, raw_path):
        client_kwargs = {
            'key': '',
            'secret': '',
            'endpoint_url': '',
            'anon': False
        }
        
        s3 = s3fs.core.S3FileSystem(**client_kwargs)
        s3.upload(rpath=raw_path, lpath=local_path)
        if s3.exists(raw_path):
            self.logger.info('File upload successfully')
        else:
            self.logger.info('File upload failed')
        

    def parse(self, response):
        if response.status == 200:
            for item in response.css('#datatable tbody tr'):
                nama = item.css('td a::text').get()
                Tahapan = item.css('td.font-tahap::text').get()
                link_detail = item.css('td a:contains("Detail")::attr(href)').get()
                raw_link_pdf = item.css('td a:contains("Download")::attr(href)').get()
                nama_clean = self.clean_name(nama)
                randomid = self.data_id_generate() 
                year = response.url.split('=')[-1]
                sub_source = 'Propemperda Tahun ' + year

                link_pdf = None if raw_link_pdf == '/download-raperda/' else raw_link_pdf
                download_pdf = None if link_pdf == None else response.urljoin(link_pdf)
                file_name_download = None if download_pdf == None else download_pdf.split('/')[-1]


                if download_pdf:
                    yield {
                        'filename' : file_name_download,
                        'file_urls': [download_pdf],
                        'sub_menu' : sub_source
                    }

                yield {
                    'nama': nama,
                    'Tahapan': Tahapan,
                    'link_pdf' : download_pdf,
                    'link_detail' : link_detail,
                    'link' :response.url,
                    'sub_menu' : sub_source
                }

                # path_raw = 'data_raw/data_icc/'
                source = 'e-legislasi_dprd_jateng'
                sub_source_path = sub_source
                format = 'json'

                path_json = 'data_elegilasi'
                dir_path = os.path.join(path_json)
                os.makedirs(dir_path, exist_ok=True)

                filename = f'{nama_clean}_{randomid}.json'
                local_path = f'D:\Visual Studio Code\Work\e-legilasi\jateng\elegilasiJateng\data_elegilasi\{filename}'
                paths3 = f's3://ai-pipeline-statistics/data/data_raw/data_icc/{source}/{sub_source_path}/json/{filename}'
                data_json = {
                    'link' : response.url,
                    'domain': 'e-legilasi.jatengprov.go.id',
                    'tag' : [
                        'https://elegislasi.dprd.jatengprov.go.id',
                        sub_source,
                        nama
                    ],
                    'crawling_time' : time.strftime("%Y-%m-%d %H:%M:%S"),
                    'crawling_time_epoch' : int(datetime.now().timestamp()),
                    'path_data_raw' : paths3,
                    'path_data_clean' : None,
                    'nama' : nama,
                    'tahapan' : Tahapan,
                    'doc_link' : link_pdf,
                    'doc_name' : file_name_download,
                }
                self.save_json(data_json, os.path.join(dir_path, filename))
                # self.upload_to_s3(local_path, paths3.replace('s3://', '') )
