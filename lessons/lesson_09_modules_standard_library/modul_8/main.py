
from data_downloader import load_df
from filter_data import tips_dfm




def main():
    order = tips_dfm
    orders = load_df(order)
    print(orders[1])



if __name__ == '__main__':
    main()

