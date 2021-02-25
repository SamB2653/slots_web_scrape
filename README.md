# Slot Web Scraping:

Scrape SlotCatalog rankings by market, with configurable scraping options.

Each market outputs a single .csv file within the output directory. Additionally, after the script has completed a file
named _all.csv will be output, containing all the data that has been scraped. Example output included.

## Configuration:

Can be changed by editing config.json

### Static Values:

These values do not need to be changed unless the site or script needs minor changes:

* **url:** The host url: "https://slotcatalog.com/en"
* **output_path:** Select the output file path, does not need to be changed unless output path needs to be changed
* **header:** Contains the user agent used by the requests module
* **data:** Used for the POST request
* **all_markets:** List of all markets available for scraping

### Scraping Options:

**start_page:** Select which page to start on (e.g. 1 would be starting on the first page):

```json
"start_page": 1
```

**top_rank:** Select the maximum rank of content scraped per market (e.g. 100 would be the top 100 ranked content):

```json
"top_rank": 100
```

**max_pages:** Set the maximum amount of pages scraped per market (e.g. 10 would be the first 10 pages):

```json
"max_pages": 10
```

**stop_on_no_rank:** If the content is not ranked then stop, this prevents N/A values (true = stop on N/A values, false
= include N/A and add artificial ranking):

```json
"stop_on_no_rank": true
```

**default_market:** Provide a single market to run the scrape on:

```json
"default_market": [
false,
{
"GB": "United Kingdom"
}
]
```

The first value is true/false:

* true = use default_market
* false = do not use default_market  
  The second value is a dictionary that contains the market code and market description. A list of these can be found in
  the "all_markets" dictionary.

**list_markets:** Provide a list of markets to run the scrape on:

```json
"list_markets": [
false,
{
"GB": "United Kingdom",
"AU": "Australia",
"AT": "Austria"
}
]
```

The first value is true/false:

* true = use list_markets
* false = do not use list_markets The second value is a dictionary that contains the market code and market description
  for each market that will be scraped. A list of these can be found in the "all_markets" dictionary.  
  
## Docker:  
Volume (local) Path:  
```
\\wsl$\docker-desktop-data\version-pack-data\community\docker\volumes\data-volume
```

Output Directory Path:  
```
\data-volume\_data\output
```

Configuration File Path:  
```
\data-volume\_data\config.json
```

Building Docker Image:  
```
docker build -t slots_web_scrape:latest .
```

Run Docker Image:  
```
docker run --rm -v data-volume:"/Python Files/slots_web_scrape/" --name scrape slots_web_scrape:latest  
```
