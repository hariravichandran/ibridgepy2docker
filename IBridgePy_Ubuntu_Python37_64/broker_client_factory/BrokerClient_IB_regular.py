#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
There is a risk of loss when trading stocks, futures, forex, options and other
financial instruments. Please trade with capital you can afford to
lose. Past performance is not necessarily indicative of future results.
Nothing in this computer program/code is intended to be a recommendation, explicitly or implicitly, and/or
solicitation to buy or sell any stocks or futures or options or any securities/financial instruments.
All information and computer programs provided here is for education and
entertainment purpose only; accuracy and thoroughness cannot be guaranteed.
Readers/users are solely responsible for how to use these information and
are solely responsible any consequences of using these information.

If you have any questions, please send email to IBridgePy@gmail.com
All rights reserved.
"""

from IBridgePy.constants import BrokerClientName
from broker_client_factory.BrokerClient_IB import ClientIB


# noinspection PyAbstractClass
class IBRegular(ClientIB):
    # !!!
    # DO NOT implement __init___ here. It will override IBCpp.__init__ and cause many errors

    @property
    def name(self):
        return BrokerClientName.IB

    def reqPositionsWrapper(self):
        self.reqPositions()

    def reqCurrentTimeWrapper(self):
        self.reqCurrentTime()

    def reqAllOpenOrdersWrapper(self):
        self.reqAllOpenOrders()

    def reqAccountUpdatesWrapper(self, subscribe, accountCode):
        self.reqAccountUpdates(subscribe, accountCode)

    def reqAccountSummaryWrapper(self, reqId, group, tag):
        self.reqAccountSummary(reqId, group, tag)

    def reqHistoricalDataWrapper(self, reqId, contract, endTime, goBack, barSize, whatToShow, useRTH, formatDate):
        # print(__name__ + '::reqHistoricalDataWrapper', endTime, goBack, barSize, whatToShow, useRTH, formatDate)
        self.reqHistoricalData(reqId, contract, endTime, goBack, barSize, whatToShow, useRTH, formatDate)

    def reqMktDataWrapper(self, reqId, contract, genericTickList, snapshot):
        self.reqMktData(reqId, contract, genericTickList, snapshot)

    def cancelMktDataWrapper(self, reqId):
        self.cancelMktData(reqId)

    def reqRealTimeBarsWrapper(self, reqId, contract, barSize, whatToShow, useRTH):
        self.reqRealTimeBars(reqId, contract, barSize, whatToShow, useRTH)

    def modifyOrderWrapper(self, contract, order, ibpyRequest):
        self.placeOrderWrapper(contract, order, ibpyRequest)

    def placeOrderWrapper(self, contract, ibcppOrder, ibpyRequest):
        if isinstance(ibcppOrder.orderId, int):
            int_orderId = ibcppOrder.orderId
        else:
            int_orderId = self.use_next_id()
            ibcppOrder.orderId = int_orderId
        self._placeOrderHelper(int_orderId, ibpyRequest, contract, ibcppOrder)

    def reqContractDetailsWrapper(self, reqId, contract):
        self.reqContractDetails(reqId, contract)

    def calculateImpliedVolatilityWrapper(self, reqId, contract, optionPrice, underPrice):
        self.calculateImpliedVolatility(reqId, contract, optionPrice, underPrice)

    def reqScannerSubscriptionWrapper(self, reqId, subscription):
        self.reqScannerSubscription(reqId, subscription)

    def cancelScannerSubscriptionWrapper(self, tickerId):
        self.cancelScannerSubscription(tickerId)

    def cancelOrderWrapper(self, ibpyOrderId):
        ibOrderId = self._idConverter.fromBrokerToIB(ibpyOrderId)
        self._log.info('cancelOrder is sent to %s ibpyOrderId=%s' % (self.name, ibpyOrderId))
        self.cancelOrder(ibOrderId)

    def reqScannerParametersWrapper(self):
        self.reqScannerParameters()

    def processMessagesWrapper(self, dummy):
        # self._log.notset(__name__ + '::processMessagesWrapper: dummyTimeNow=%s' % (dummy,))
        self.processMessages()  # IBCpp function
