import json
import os
import random
import re
import time
import timeit
import numpy as np
import pandas as pd
import requests
from pathlib import Path
from bs4 import BeautifulSoup


def read_json():
    try:
        dir_path = Path(__file__).parent
        input_path = Path.joinpath(dir_path, "config.json")
        with open(input_path, "r") as json_file:
            data = json_file.read()
        json_out = json.loads(data)
        return json_out
    except json.decoder.JSONDecodeError as e:
        print(f"JSON read error: {e}")
    except FileNotFoundError as e:
        print(f"Configuration file not found: {e}")


def options():
    pd.set_option("display.max_rows", 500)
    pd.set_option("display.max_columns", 500)
    pd.set_option("display.width", 1000)


def get_response(url, session, data_x, header):
    session.headers.update(header)
    response = session.request("POST", url, data=data_x)
    soup = BeautifulSoup(response.text, "lxml")
    return soup


def scrape(session, url, df, data_x, header):
    soup = get_response(url, session, data_x, header)  # POST request returns HTML, parse with lxml parser

    content_info_dict = {
    }  # store each provider card here

    card_count, is_rank_value = 0, True  # default values
    for provider_card in soup.find_all("div", class_="providerCard"):  # isolate provider card
        for name in provider_card.find_all("a", class_="providerName"):  # get content name
            content_info_dict["Name"] = [str(name.get("title"))]

        for rank in provider_card.find_all("span", class_="widgetSRBIG-small-pr"):  # get content rank
            if rank.text.isdigit():  # check if int value, if not then end as N/A after and content not within market
                content_info_dict["Rank"] = [str(rank.text)]
            else:
                content_info_dict["Rank"] = [np.nan]  # NaN value
                is_rank_value = False

        for casino in provider_card.find_all("p", class_="providerCard-prewBlock-number"):  # get casino count
            if casino.text.isdigit():
                content_info_dict["Casinos"] = [str(casino.text)]
            else:
                content_info_dict["Casinos"] = [np.nan]

        for provider_real in provider_card.find_all("img", alt="logo"):
            content_info_dict["Provider"] = [str(provider_real.get("title"))]

        data = pd.DataFrame(content_info_dict)  # temp data storage of dict
        df = df.append(data, ignore_index=True)  # add to main storage
        card_count += 1

    rand_wait = round(random.uniform(0.5, 1.0), 2)
    time.sleep(rand_wait)
    print(f'Page: {data_x["p"]} | Content: {card_count} | Random Sleep: {rand_wait}s | Market: {data_x["cISO"]}')
    return df, card_count, is_rank_value


def format_data(df, market):
    df["Market"] = market
    today_date = pd.to_datetime('today').normalize()
    df["Date"] = today_date

    config = read_json()
    if config["stop_on_no_rank"]:  # if stop on NaN ranking, remove any NaN rankings (config)
        df = df[df["Rank"].notnull()]

    df_format = df.copy(deep=True)  # stop SettingCopyWarning

    try:
        df_format["Casinos"] = df_format["Casinos"].fillna(0)  # when 1 casino this field is NaN if there is a rank
    except KeyError as e:
        print(f"Adding Casino Column: {e}")  # rare case when testing
        df_format["Casinos"] = 1

    df_format["NameInternal"] = [re.sub(r"\([^)]*\)", "", str(x)) for x in df_format["Name"]]  # remove text in brackets
    df_format["NameInternal"] = [re.sub(r"[^A-Za-z0-9]", "", str(x.lower())) for x in df_format["NameInternal"]]
    df_format["ProviderInternal"] = [re.sub(r"[^A-Za-z0-9]", "", str(x.lower())) for x in df_format["Provider"]]

    if not config["stop_on_no_rank"]:  # if no stop on NaN rank, then order based on index to replace NaN
        df_format["Rank"] = df_format.index + 1

    df_format[["Name", "Provider", "Market", "NameInternal", "ProviderInternal"]] = df_format[
        ["Name", "Provider", "Market", "NameInternal", "ProviderInternal"]].astype("string")
    df_format[["Rank", "Casinos"]] = df_format[["Rank", "Casinos"]].astype("int64")

    try:
        df_format = df_format[~(df_format['Rank'] > config["top_rank"])]  # remove values over top rank (config)
    except TypeError as e:
        print(f"NaN found, skipping top rank removal: {e}")

    print(f"Data format complete: {market} | {today_date} | NaN ranks removed | 0 value Casino fixed | "
          f"Internal Columns added | Data types updated")
    return df_format


def write_data(df, file_name, mode):
    config = read_json()
    output_path = config["output_path"]
    dir_path = Path(__file__).parent  # dir_path = Path(__file__).parent.parent when one level higher

    if mode == "all":
        path = Path.joinpath(dir_path, output_path, file_name)
        df.to_csv(path, encoding="utf-8", index=False, mode="w")  # utf-8 encoding
        print(f"Saved to: {path} | 'all' mode")
    if mode == "local":
        path = Path.joinpath(dir_path, output_path, file_name)
        df.to_csv(path, encoding="utf-8", index=False, mode="w")  # utf-8 encoding
        print(f"Saved to: {path} | 'local' mode")


def per_market(config, session, url, market):
    start = timeit.default_timer()
    df = pd.DataFrame()  # blank data frame for total output
    page, data, header = config["start_page"] - 1, config["data"], config["header"]  # from config
    data_available, relative_page, total_content = True, 0, 0  # data_available: True when request returns data

    while data_available:
        page += 1
        relative_page += 1

        config["data"]["p"] = page  # set data sent within POST request to page number
        config["data"]["cISO"] = market  # set data sent within POST request to market selection

        df, card_count, is_rank_value = scrape(session, url, df, data, header)
        total_content += card_count

        if card_count == 0:  # stop if no more content in response
            break
        if not is_rank_value and config["stop_on_no_rank"]:  # stop if no more content in response (true in config)
            break
        if total_content > config["top_rank"]:  # stop if exceeded max rank collected per market (set in config)
            print(f"{total_content} content scraped for {market}, stopped due to limit of {config['top_rank']} entries")
            break
        if relative_page == config["max_pages"]:  # relative page, not real page number break condition
            print(f"Stopped after {relative_page} pages due to set limit of {config['max_pages']}")
            break

    df = format_data(df, market)  # format and add columns to data
    stop = timeit.default_timer()
    execution_time = round((stop - start), 2)
    execution_page_avg = round(execution_time / relative_page, 2)
    print(f"{market} data took {str(execution_time)}s ({round(execution_time / 60, 2)}min) to execute | "
          f"Per page: {str(execution_page_avg)}s")
    return df


def market_selection(config):
    if config["default_market"][0] and not config["list_markets"][0]:
        select_markets = config["default_market"][1]  # for default (one market)
        print("Using 'default_market'")
    elif not config["default_market"][0] and config["list_markets"][0]:
        select_markets = config["list_markets"][1]  # for list (multiple markets)
        print("Using 'list_markets'")
    elif not config["default_market"][0] and not config["list_markets"][0]:
        select_markets = config["all_markets"]  # for all (all markets)
        print("Using 'all_markets'")
    else:
        select_markets = config["all_markets"]  # for all (all markets) - when true for default_market and list_markets
        print("Using 'all_markets' ('default_market' and 'list_markets' are both set to true)")
    return select_markets


def main():
    start = timeit.default_timer()
    options()
    config = read_json()
    print(f"Config file loaded: {os.path.realpath('config.json')}")  # config path
    url = config["url"]
    print(f"URL: {url}")

    df_all = pd.DataFrame()  # blank data frame
    session = requests.Session()  # persistent session for requests
    markets = market_selection(config)  # select all, some or one market to scrape

    run_num = 0
    for m_code, m_value in markets.items():
        print(f"Market selected: {m_value} ({m_code})")

        df = per_market(config, session, url, m_code)  # return data frame with market specific data

        write_data(df, f"{m_code}.csv", "local")  # append to file (one file per market)

        df_all = df_all.append(df, ignore_index=True)  # add to main storage
        print(f"Added {m_value} ({m_value}) data to main data set | {df_all.shape[0]} total rows")
        run_num += 1

    write_data(df_all, "_all.csv", "all")  # save all markets data to csv (write to new file)
    print("Saved combined data")

    stop = timeit.default_timer()
    execution_time = round((stop - start), 2)
    execution_country_avg = round(execution_time / run_num, 2)
    print(f"Script took {str(execution_time)}s ({round(execution_time / 60, 2)}min) to execute | "
          f"Per Country: {str(execution_country_avg)}s")


if __name__ == '__main__':
    main()
