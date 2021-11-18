from operator import attrgetter

import numpy as np
import pandas as pd

from rounds.models import *


class Principle(Enum):
    """
    Enumeration for the market principle used to determine the market price.
    These are set forth according to:  Sun et al. (2010)
    https://www.researchgate.net/publication/241567616_Algorithm_of_Call_Auction_Price
    """
    VOLUME = 1
    RESIDUAL = 2
    PRESSURE = 3
    REFERENCE = 4
    NO_ORDERS = 5


def ensure_tuple(obj):
    if type(obj) == tuple:
        return obj
    else:
        return obj.price, obj.quantity


def get_cxq(price, orders, otype):
    """
    Determine the cumulative buy/sell quantity for the given price with the give
    market orders. The orders should be a list-like of tuples each containing a
    price / quantity pair. That list is summed by price.
    If the order type is OrderType.BID then, find all prices equal to or greater
    than the given price and add up there respective quantities.
    For OrderType.OFFER, find all price equal to or less than the given price
    and sum the respective quantities.

    Parameters
        price (number): The reference price used in filtering the list of orders
        orders (list-like): The list of orders.  This list should consist of
                    tuples of price/ quantity pairs.
        otype (OrderType): This controls how the list of orders are compared to the
                    reference price.  If the otype == OrderType.BID then consider
                    prices greater or equal to the reference price.   Less then or
                    equal to the reference price for otype == OrderType.OFFER

    Returns:
        (number): The Cumulative Buy/Sell Quantity for the given price
    """

    if orders is None or len(orders) == 0:
        return 0

    # reduce orders list
    df = pd.DataFrame(orders, columns=['price', 'volume'])
    reduced = df.groupby('price').sum().reset_index()

    if otype == OrderType.BID:
        quantity_base = reduced[reduced.price >= price]
    else:
        quantity_base = reduced[reduced.price <= price]

    return quantity_base.volume.sum()


def ensure_tuples(bids, offers):
    # Ensure input data is in the form of price/quant tuples
    if bids:
        bids = [ensure_tuple(o) for o in bids]

    if offers:
        offers = [ensure_tuple(o) for o in offers]

    return bids, offers


class MarketPrice:
    """
    Implementation of the Call Market price algorithm described by: Sun et al. (2010)
    https://www.researchgate.net/publication/241567616_Algorithm_of_Call_Auction_Price
   
    Usage:
       mp = MarketPrice(bids, offers)
       price, volume = mp.get_market_price(last_price = <number>)

       The bids and offers can be either lists of Orders or (price/quantity) tuples.

       Parameters:
       bids, offers:   The bids and offers passed into the constructed. They will be lists
                        of (price/quantity) tuples
        has_bids, has_offers:  True if the bids or offers (respectively) are non_null and
                            non-empty.
        price_df:  The pandas DataFrame that is use to process the price.  Accessing this
                    is useful for debugging since is contains a history of the algorithm's
                    progress
        final_principle:  The last Principle that the algorithm attempted to apply
    """

    def __init__(self, bids, offers):
        bids, offers = ensure_tuples(bids, offers)
        self.bids, self.offers = bids, offers

        self.has_bids = bids is not None and len(bids) > 0
        self.has_offers = offers is not None and len(offers) > 0
        self.price_df = None
        self.final_principle = None
        self.candidate_prices = None

        # 1 get all prices
        if self.has_bids and self.has_offers:
            all_orders = np.concatenate((bids, offers))
        else:
            return

        # if there are orders, then create the main data frame to carry the
        # price calculation

        # Assemble all orders into one DataFrame and group by price
        all_orders_df = pd.DataFrame(all_orders, columns=['price', 'volume'])
        # Resetting the index ensures that there is a 'price' column
        self.price_df = all_orders_df.groupby('price').sum().reset_index()

    def get_mev(self):

        # Get the mevs associated with the market price
        mevs = self.price_df[self.price_df.market_price].mev.values

        if len(mevs) != 1:
            raise ArgumentError("Found {} market prices, there should be exactly 1".format(len(mevs)))

        return int(mevs[0])

    def only_one_candidate_price(self):
        return sum(self.candidate_prices) == 1

    def finalize_and_get_result(self):
        if not self.only_one_candidate_price():
            raise ArgumentError("Found {} market prices, there should be exactly 1".format(len(mevs)))

        market_price = self.price_df[self.candidate_prices].price.values[0]

        self.price_df['market_price'] = self.price_df.price == market_price
        mev = self.get_mev()
        return market_price, mev

    def apply_max_volume_princ(self):
        self.final_principle = Principle.VOLUME

        # 2 PRINCIPLE OF MAXIMUM VOLUME
        # 2.1 Calculate cumulative buy / sell quantities
        self.price_df['cbq'] = self.price_df.price.apply(get_cxq, args=(self.bids, OrderType.BID))
        self.price_df['csq'] = self.price_df.price.apply(get_cxq, args=(self.offers, OrderType.OFFER))

        # 2.2 Maximum exchange volume.   For each price, the MEV is min{cbq, csq}
        self.price_df['mev'] = self.price_df[['cbq', 'csq']].apply(min, axis=1)

        # 2.3  The prices with the highest MEV are the candidate prices
        self.candidate_prices = self.price_df.mev == max(self.price_df.mev)
        self.price_df['max_volume_cand'] = self.candidate_prices

    def apply_least_residual_princ(self):
        self.final_principle = Principle.RESIDUAL

        # 3.1  Calculate the residual volume (Left volume, LV)
        self.price_df.loc[self.candidate_prices, 'residual'] = (self.price_df.cbq - self.price_df.csq).apply(abs)

        # 3.2  Prices associated with the minimum residual volume are candidate prices
        min_resid = min(self.price_df[self.candidate_prices].residual)
        self.candidate_prices = self.price_df.residual == min_resid
        self.price_df['min_res_cand'] = self.candidate_prices

    def apply_market_pressure_princ(self):
        self.final_principle = Principle.PRESSURE

        self.price_df.loc[self.candidate_prices, 'buy_pressure'] = (self.price_df.cbq >= self.price_df.csq).astype(int)
        self.price_df['pressure_cand'] = False

        # 4.1.a If the minimum residual process produced prices where CBQ >= CSQ
        # then take the max of such a price
        # This is a candidate price
        buy_press_mask = self.price_df.buy_pressure == 1
        if not self.price_df[buy_press_mask].empty:
            max_buy_price = max(self.price_df[buy_press_mask].price)
            self.price_df.loc[self.price_df.price == max_buy_price, 'pressure_cand'] = True

        # 4.1.b If the minimum residual process produced prices where CBQ < CSQ
        # then take the min of such a price
        # This is a candidate price
        sell_press_mask = self.price_df.buy_pressure == 0
        if not self.price_df[sell_press_mask].empty:
            min_sell_price = min(self.price_df[sell_press_mask].price)
            self.price_df.loc[self.price_df.price == min_sell_price, 'pressure_cand'] = True

        self.candidate_prices = self.price_df.pressure_cand

    def apply_reference_price_princ(self):
        self.final_principle = Principle.REFERENCE
        ##
        # This stuff commented out is a faithful implementation of the reference price
        # principle.   However, our goal is to drive prices up.  So, if the price selection
        # gets to this point, we'll choose the highest price.
        ##

        # 5.1 pick the price that was closest to the last market price
        # price_df['last_market_price'] = last_market_price
        # price_df.loc[candidate_prices, 'delta'] = (price_df.price - last_market_price).apply(abs)
        # min_diff = min(price_df[candidate_prices].delta)
        # market_price = price_df[price_df.delta == min_diff].price.values[0]

        # pick the highest price
        market_price = max(self.price_df.loc[self.candidate_prices].price.values)
        self.price_df['reference_cand'] = self.price_df.price == market_price
        self.candidate_prices = self.price_df.reference_cand

    def get_market_price(self, last_price=0):
        """
        Implementation of the Call Market price algorithm described by: Sun et al. (2010)
        https://www.researchgate.net/publication/241567616_Algorithm_of_Call_Auction_Price
        
           Parameters: 
                last_price (number) - This is the reference price used in
                                            last principle.  (Reference)  This should be
                                            rarely used as most markets pick a unique price
                                            based on the principle of maximum volume
            
            Return:
                A tuple containing
                market_price (number): The resulting market price
                volume (number):  the Market Exchange Volume
                principle (Principle):  Enum representing the final principle applied
                                        to the determine the price.  Useful for testing
                df (DataFrame):  Pandas DataFrame containing the results of each principle.
                                This is useful for debugging.
        """

        #  Handle error cases where there are missing bids or offers
        if not (self.has_bids and self.has_offers):
            self.final_principle = Principle.NO_ORDERS
            return last_price, 0

        #  2 PRINCIPLE OF MAXIMUM VOLUME
        self.apply_max_volume_princ()
        if self.only_one_candidate_price():
            return self.finalize_and_get_result()

        #  3 PRINCIPLE OF MINIMUM RESIDUAL
        self.apply_least_residual_princ()
        if self.only_one_candidate_price():
            return self.finalize_and_get_result()

        #  4 PRINCIPLE OF MARKET PRESSURES
        self.apply_market_pressure_princ()
        if self.only_one_candidate_price():
            return self.finalize_and_get_result()

        # 5 PRINCIPLE OF REFERENCE PRICES
        self.apply_reference_price_princ()
        return self.finalize_and_get_result()  # at this point, we are guaranteed one price


# END MarketPrice

def count_filled_volume(orders):
    """
    Helper function to count the total volume of orders filled of a given list of Orders.
    Parameters:
        orders (list: Order):  The list of orders

    Returns:
        (number) the total filled volume of the list
    """
    return sum([o.quantity_final or 0 for o in orders])


def partial_fill(order_list, cap):
    """
    Given a list of Orders (ideally sorted by price), determine which orders to fill.
    Quantities of the orders will be adjusted so that the sum of the resulting list
    will be equal to the cap.   Orders are iterated through in the given order
    (this function will not sort the list). If the quantity of the current order
    does not cause the running total to exceed the cap then it is copied into the
    return list.   If the current order does cause the total quantity to exceed the
    cap, then the order is copied into the return list with a modified amount so
    that the total quantity of the return list equals the cap.

        Parameters:
            order_list (list-like: Order) The list of orders (should be pre-sorted)
                            prior to call.
            cap (number): The cap amount.  The total quantity of the returned order list
                                will match this amount

        Returns:
            A list of orders modified in such a way that the combined quantity equals the
            given cap.
    """
    ret_list = []
    # If there is a zero cap, then there is no need to do anything else
    if cap == 0 or order_list is None or not order_list:
        return ret_list

    # If we make it here, we still need to deal with partial orders
    # Accumulate volumes in the partial order list, until we have surpassed the mev
    accumulated_volume = 0
    idx = 0
    while accumulated_volume < cap:
        order = order_list[idx]
        order.quantity_final = order.quantity
        accumulated_volume += order.quantity
        idx += 1
        ret_list.append(order)

    # at this point, the last order added to the filled_order list should be
    #  "too much".   Adjust that order by the difference of accum - cap.
    last_order = ret_list[-1]
    last_order.quantity_final = last_order.quantity - (accumulated_volume - cap)

    return ret_list


def count_volume(orders):
    """
    Helper function to count the total volume of a given list of Orders.
    Parameters:

    Returns:
        (number, number) a tuple that contains the volumes of bids and offers
    """
    vol = sum([o.quantity for o in orders])

    return vol


class OrderFill:
    SORT_KEY = attrgetter('price', 'quantity')

    def __init__(self, orders):
        """
        Split the given orders into bids and offers and sorts them by price and quantity
        """
        self.orders = orders

        self.bids = [o for o in orders if o.order_type == OrderType.BID.value]
        self.bids.sort(key=OrderFill.SORT_KEY, reverse=True)

        self.offers = [o for o in orders if o.order_type == OrderType.OFFER.value]
        self.offers.sort(key=OrderFill.SORT_KEY)

    def select_bids(self, thold_price):
        """
        Select orders with a price less than or equal to the threshold price.
        Parameters:
            thold_price (number):  The threshold price
        Returns:
            (list: Order): A list of orders with price less than or equal to the threshold price
        """

        return list(filter(lambda o: o.price >= thold_price, self.bids))

    def select_offers(self, thold_price):
        """
        Select orders with a price greater than or equal to the threshold price.
        Parameters:
            thold_price (number):  The threshold price
            
        Returns:
            (list: Order): A list of orders with price greater than or equal to the threshold price
        """
        return list(filter(lambda o: o.price <= thold_price, self.offers))

    def fill_orders(self, market_price):
        """
        Determine which orders to fill. Sets the 'quantity_final' on all transacted orders.
        Note most 'quantity_final's will be the same as the order quantity.  A few might be different to
        ensure the market volume is met.
        """

        # Sort and filter bids and offers
        bids_to_exchange = self.select_bids(market_price)
        offers_to_exchange = self.select_offers(market_price)

        total_volume_bid = count_volume(bids_to_exchange)
        total_volume_offer = count_volume(offers_to_exchange)
        mev = min(total_volume_bid, total_volume_offer)

        if total_volume_bid < total_volume_offer:
            # All bids will be traded - offers should be modified
            filled_bids = bids_to_exchange
            for o in filled_bids:
                o.quantity_final = o.quantity
            filled_offers = partial_fill(offers_to_exchange, mev)

        elif total_volume_bid > total_volume_offer:
            # All offers will be traded - bids are modified.
            filled_bids = partial_fill(bids_to_exchange, mev)
            filled_offers = offers_to_exchange
            for o in filled_offers:
                o.quantity_final = o.quantity

        else:
            # All orders are traded and we're done
            filled_bids = bids_to_exchange
            for o in filled_bids:
                o.quantity_final = o.quantity
            filled_offers = offers_to_exchange
            for o in filled_offers:
                o.quantity_final = o.quantity

        return filled_bids, filled_offers
