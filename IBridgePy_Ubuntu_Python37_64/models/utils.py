from IBridgePy.constants import OrderType


def print_IBCpp_contract(contract):
    """
    IBCpp.Contract() cannot use __str__ to print so that make a print-function
    :param contract: IBCpp.Contract()
    :return: String
    """
    base = ['secType', 'primaryExchange', 'exchange', 'symbol', 'currency']
    stkCash = base
    fut = base + ['expiry']
    other = fut + ['strike', 'right', 'multiplier', 'localSymbol']
    ans = '{'
    if contract.secType in ['STK', 'CASH']:
        iterator = stkCash
    elif contract.secType in ['FUT', 'BOND']:
        iterator = fut
    else:
        iterator = other
    for para in iterator:
        ans += str(getattr(contract, para)) + ','
    return ans[:-1] + '}'


def print_IBCpp_order(order):
    """
    IBCpp.Order() cannot use __str__ to print so that make a print-function
    :param order: IBCpp.Order()
    :return: String
    """
    action = order.action  # BUY, SELL
    amount = order.totalQuantity  # int only
    orderType = order.orderType  # LMT, MKT, STP
    tif = order.tif
    orderRef = order.orderRef

    ans = '{account=%s action=%s orderType=%s amount=%s tif=%s orderRef=%s' % (order.account, action, orderType, amount, tif, orderRef)
    if orderType == OrderType.MKT:
        pass
    elif orderType == OrderType.LMT:
        ans += ' limitPrice=' + str(order.lmtPrice)
    elif orderType == OrderType.STP:
        ans += ' stopPrice=' + str(order.auxPrice)
    elif orderType == OrderType.TRAIL_LIMIT:
        if order.auxPrice < 1e+307:
            ans += ' trailingAmount=' + str(order.auxPrice)
        if order.trailingPercent < 1e+307:
            ans += ' trailingPercent=' + str(order.trailingPercent)
        ans += ' trailingStopPrice=' + str(order.trailStopPrice)
    elif orderType == OrderType.TRAIL:
        if order.auxPrice < 1e+307:
            ans += ' trailingAmount=' + str(order.auxPrice)
        if order.trailingPercent < 1e+307:
            ans += ' trailingPercent=' + str(order.trailingPercent)
        if order.trailStopPrice < 1e+307:
            ans += ' trailingStopPrice=' + str(order.trailStopPrice)
    ans += '}'
    return ans


def print_IBCpp_orderState(orderState):
    return '{status=%s commission=%s warningText=%s}' % (orderState.status, orderState.commission, orderState.warningText)


def print_IBCpp_execution(execution):
    return '{orderId=%s clientId=%s time=%s acctNumber=%s exchange=%s side=%s shares=%s price=%s}' \
           % (execution.orderId, execution.clientId, execution.time, execution.acctNumber, execution.exchange,
              execution.side, execution.shares, execution.price)


def print_IBCpp_contractDetails(contractDetails):
    ans = '{'
    for item in ['marketName', 'minTick', 'priceMagnifier', 'orderTypes', 'validExchanges', 'underConId',
                 'longName', 'contractMonth', 'industry', 'category', 'subcategory', 'timeZoneId',
                 'tradingHours', 'liquidHours', 'evRule', 'evMultiplier', 'mdSizeMultiplier', 'aggGroup',
                 'secIdList', 'underSymbol', 'underSecType', 'marketRuleIds', 'realExpirationDate', 'cusip',
                 'ratings', 'descAppend', 'bondType', 'couponType', 'callable', 'putable', 'coupon',
                 'convertible', 'maturity', 'issueDate', 'nextOptionDate', 'nextOptionType',
                 'nextOptionPartial', 'notes']:
        try:
            if hasattr(contractDetails, item):
                ans += '%s=%s ' % (item, getattr(contractDetails, item))
        except TypeError:
            pass
            # Some items in the item list does not exist for some requests. If it happens, Python3x will fail for the following Error
            # File "ibpyRoot/models/utils.py", line 84, in print_IBCpp_contractDetails
            # if hasattr(contractDetails, item):
            # TypeError: No Python class registered for C++ class shared_ptr<std::__1::vector<shared_ptr<TagValue>, std::__1::allocator<shared_ptr<TagValue> > > >
    if contractDetails.summary:
        ans += 'contract=%s' % (print_IBCpp_contract(contractDetails.summary),)
    return ans + '}'
