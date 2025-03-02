import scrapy
import pandas as pd

class TableSpider(scrapy.Spider):
    name = 'table_spider'
    start_urls = ['https://en.wikipedia.org/wiki/List_of_highest-grossing_films']
    
    def parse(self, response):
        h2 = response.xpath('//div[@class="mw-heading mw-heading2"]')[0]
        table = h2.xpath('following-sibling::table')[0]
        rows = table.xpath('.//tbody/tr')

        data=[]
        for i in range(len(rows)):
            row=rows[i]
            data_from_table = row.xpath('.//td | .//th')  # Select all cells (td for data, th for headers)
            data_from_table = [cell.xpath('normalize-space(.)').get() for cell in data_from_table]
            data.append(data_from_table)
    
        columns = ["Rank", "Peak", "Film Title", "Worldwide gross", "Release Year", "Ref"]
        df = pd.DataFrame(data, columns=columns)
        df.to_csv('table.csv', index=False)
        self.logger.info(f"Extracted DataFrame:\n{df}")
        
        # From obtained links, parse into separate df
        links = rows.xpath('.//th[@scope="row"]/i/a/@href').getall()
        for link in links:
            # go to link, parse data
            link = response.urljoin('https://en.wikipedia.org'+link)  # Construct full URL
            yield scrapy.Request(url=link, callback=self.parse_film_page)
            # data.append(box_data)
        
    def parse_film_page(self, response):
        box = response.xpath('//div[@class="mw-content-ltr mw-parser-output"]')[0]
        table = box.xpath('.//table[@class="infobox vevent"]')[0]
        rows = table.xpath('.//tbody/tr')
        
        info = {"Directed by": None, "Country": None, "Box office": None, "Name":None}  # Dictionary to store values
        target_rows = ["Directed by", "Countries", "Box office", "Country"]

        for row in rows:
            header = row.xpath('.//th[@scope="row"]/text()').get()
            if header in target_rows:
                
                if header == "Countries" or header == "Country":
                    value = row.xpath('.//td//text()').get()
                    if value=="\n" or not value:
                        value = row.xpath('.//td[@class="infobox-data"]//li[1]/text()').get()
                    if value=="" or not value:
                        value = row.xpath('.//td[@class="plainlist"]//li[1]/text()').get()
                    info["Country"] = value
                        
                elif header == "Directed by":
                    value = row.xpath('.//td//text()').get()
                    if value and len(value) > 30:  # Means it is actually list of authors
                        value = row.xpath('.//td[@class="infobox-data"]/text()').get()
                        if not value or value=="":
                            value=row.xpath('.//td[@class="infobox-data"]//li[1]//a/text()').get()
                            if not value or value=="":
                                value=row.xpath('.//td[@class="infobox-data"]//li[1]//text()').get()
                    info["Directed by"] = value
                    
                elif header == "Box office":
                    value = row.xpath('.//td//text()').get()
                    info["Box office"] = value
                    
        name=rows[0].xpath('.//th//text()').getall()
        name=' '.join(name).strip()
        info["Name"]=name
        
        # Create DataFrame from the dictionary
        columns=["Directed by", "Box office", "Country"]
        df_infobox = pd.DataFrame([info])
        # Append to csv without column name
        df_infobox.to_csv('box.csv', mode='a', index=False, header=False)
        self.logger.info(f"Extracted infobox data for {response.url}")