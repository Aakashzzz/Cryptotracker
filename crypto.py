import time
import pandas as pd
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def setup_driver():
    options = Options()

    # options.add_argument("--headless=new")

    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )


def scrape_100_coins(driver):
    driver.get("https://coinmarketcap.com/?page=1")
    time.sleep(8)

    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")
    collected_coins = {}

    previous_total = 0
    unchanged_attempts = 0
    max_unchanged_attempts = 10

    while (
        len(collected_coins) < 100
        and unchanged_attempts < max_unchanged_attempts
    ):
        rows = driver.find_elements(By.XPATH, "//table/tbody/tr")

        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")

                if len(cells) < 8:
                    continue

                coin_name = row.find_element(
                    By.XPATH,
                    ".//p[contains(@class, 'coin-item-name')]",
                ).text.strip()

                if not coin_name or "Index" in coin_name:
                    continue

                rank_text = cells[1].text.strip()
                price = cells[3].text.strip()
                change_24h = cells[4].text.strip()
                market_cap = cells[7].text.strip()

                collected_coins[coin_name] = {
                    "Timestamp": timestamp,
                    "Rank": rank_text,
                    "Coin Name": coin_name,
                    "Price": price,
                    "24H Change": change_24h,
                    "Market Cap": market_cap,
                }

            except Exception:
                continue

        current_total = len(collected_coins)
        print(f"Coins collected: {current_total}")

        if current_total == previous_total:
            unchanged_attempts += 1
        else:
            previous_total = current_total
            unchanged_attempts = 0

        driver.execute_script(
            """
            window.scrollBy({
                top: Math.max(window.innerHeight * 0.8, 600),
                left: 0,
                behavior: "smooth"
            });
            """
        )

        time.sleep(2)

    coins = list(collected_coins.values())

    def rank_value(coin):
        try:
            return int(coin["Rank"])
        except (TypeError, ValueError):
            return 999999

    coins.sort(key=rank_value)
    coins = coins[:100]

    # Guarantee sequential ranks if CoinMarketCap's rank cell was unavailable.
    for index, coin in enumerate(coins, start=1):
        if rank_value(coin) == 999999:
            coin["Rank"] = index

    return coins


def main():
    driver = setup_driver()

    try:
        crypto_data = scrape_100_coins(driver)

        df = pd.DataFrame(
            crypto_data,
            columns=[
                "Timestamp",
                "Rank",
                "Coin Name",
                "Price",
                "24H Change",
                "Market Cap",
            ],
        )

        print("\n", df.to_string(index=False))
        print(f"\nTotal coins scraped: {len(df)}")

        output_file = "crypto_100_coins.csv"
        df.to_csv(output_file, index=False, encoding="utf-8-sig")

        print(f"\nData saved to {output_file}")

        if len(df) < 100:
            print(
                "\nWarning: CoinMarketCap returned only "
                f"{len(df)} accessible coin rows."
            )

    finally:
        driver.quit()


if __name__ == "__main__":
    main()