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
import datetime as dt
from sys import exit

import pandas as pd

from BasicPyLib.BasicTools import epoch_to_dt, dt_to_epoch
from IBridgePy.IbridgepyTools import stripe_exchange_primaryExchange_from_contract
from IBridgePy.quantopian import from_contract_to_security
from broker_client_factory.BrokerClient import BrokerClientBase
from broker_client_factory.BrokerClientDefs import ReqAttr
from broker_client_factory.CustomErrors import CustomError
from models.AccountInfo import UpdateAccountValueRecord, AccountSummaryRecord
from models.Data import TickPriceRecord, TickSizeRecord, TickStringRecord, TickOptionComputationRecord
from models.Order import OrderStatusRecord, OpenOrderRecord, ExecDetailsRecord
from models.Position import PositionRecord
from models.utils import print_IBCpp_contract, print_IBCpp_order, print_IBCpp_orderState, print_IBCpp_execution, \
    print_IBCpp_contractDetails

# https://www.interactivebrokers.com/en/software/api/apiguide/tables/tick_types.htm
MSG_TABLE = {0: 'bid size', 1: 'bid price', 2: 'ask price', 3: 'ask size',
             4: 'last price', 5: 'last size', 6: 'daily high', 7: 'daily low',
             8: 'daily volume', 9: 'close', 14: 'open', 27: 'option call open interest', 28: 'option put open interest'}


# noinspection PyAbstractClass
class CallBacks(BrokerClientBase):
    def accountDownloadEnd(self, accountCode):
        """
        Responses of reqAccountUpdates
        """
        self._log.debug(__name__ + '::accountDownloadEnd: accountCode=%s' % (accountCode,))
        self._activeRequests.set_all_requests_of_a_reqType_to_a_status('reqAccountUpdates', ReqAttr.Status.COMPLETED)

    def accountSummary(self, reqId, accountCode, tag, value, currency):
        """
        !!!!!!!! type(value) is STRING !!!!!!!!
        """
        self._log.notset(__name__ + '::accountSummary: reqId=%s accountCode=%s tag=%s value=%s currency=%s'
                         % (str(reqId), accountCode, tag, str(value), currency))
        if not isinstance(value, float):
            value = float(value)
        self._singleTrader.set_accountSummary(self.brokerName, accountCode,
                                              AccountSummaryRecord(reqId, accountCode, tag, value, currency))

    def accountSummaryEnd(self, reqId):
        self._log.debug(__name__ + '::accountSummaryEnd: ' + str(reqId))
        self._activeRequests.set_a_request_of_a_reqId_to_a_status(reqId, ReqAttr.Status.COMPLETED)

    def bondContractDetails(self, reqId, contractDetails):
        """
        IB callback function to receive str_security info
        """
        self._log.info(__name__ + '::bondContractDetails:' + str(reqId))
        aRequest = self._activeRequests.get_by_reqId_otherwise_exit(reqId)
        newRow = pd.DataFrame({'right': contractDetails.summary.right,
                               'strike': float(contractDetails.summary.strike),
                               # 'expiry':dt.datetime.strptime(contractDetails.summary.expiry, '%Y%m%d'),
                               'expiry': contractDetails.summary.expiry,
                               'contractName': print_IBCpp_contract(contractDetails.summary),
                               'str_security': contractDetails.summary,
                               'multiplier': contractDetails.summary.multiplier,
                               'contractDetails': contractDetails
                               }, index=[len(aRequest.returnedResult)])
        aRequest.returnedResult = aRequest.returnedResult.append(newRow)

    def commissionReport(self, commissionReport):
        self._log.notset(__name__ + '::commissionReport: DO NOTHING' + str(commissionReport))

    def contractDetails(self, reqId, contractDetails):
        """
        IB callback function to receive str_security info
        """
        self._log.notset(__name__ + '::contractDetails: reqId=%s contractDetails=%s' % (reqId, print_IBCpp_contractDetails(contractDetails)))
        aRequest = self._activeRequests.get_by_reqId_otherwise_exit(reqId)
        newRow = pd.DataFrame({'right': contractDetails.summary.right,
                               'strike': float(contractDetails.summary.strike),
                               'expiry': contractDetails.summary.expiry,
                               'contractName': print_IBCpp_contract(contractDetails.summary),
                               'security': from_contract_to_security(contractDetails.summary),
                               'contract': contractDetails.summary,
                               'multiplier': contractDetails.summary.multiplier,
                               'contractDetails': contractDetails
                               }, index=[len(aRequest.returnedResult)])
        aRequest.returnedResult = aRequest.returnedResult.append(newRow)

    def contractDetailsEnd(self, reqId):
        """
        IB callback function to receive the ending flag of str_security info
        """
        self._log.debug(__name__ + '::contractDetailsEnd:' + str(reqId))
        self._activeRequests.set_a_request_of_a_reqId_to_a_status(reqId, ReqAttr.Status.COMPLETED)

    def currentTime(self, tm):
        """
        IB C++ API call back function. Return system time in datetime instance
        constructed from Unix timestamp using the showTimeZone from MarketManager
        """
        serverTime = epoch_to_dt(float(tm))
        self._log.debug(__name__ + '::currentTime: tm=%s brokerClientId=%s' % (serverTime, id(self)))
        self._timeGenerator.set_diffBetweenLocalAndServer(serverTime)
        self._activeRequests.set_all_requests_of_a_reqType_to_a_status('reqCurrentTime', ReqAttr.Status.COMPLETED)

    def error(self, errorId, errorCode, errorMessage):
        """
        errorId can be either reqId or orderId or -1
        only print real error messages, which is errorId < 2000 in IB's error
        message system, or program is in debug mode
        """
        self._log.debug(__name__ + '::error: errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorMessage))
        if errorCode in [501, 326]:  # Do nothing
            # errorCode=501 errorMessage=Already connected.
            # errorCode=326 errorMessage=Unable to connect as the client id is already in use. Retry with a unique client id.
            return
        if errorCode in [502]:
            # errorCode:502 errorId:-1 errorMessage=Couldn't connect to TWS.  Confirm that "Enable ActiveX and Socket Clients" is enabled on the TWS "Configure->API" menu.
            self._log.error('Hint 1: Enable API.')
            self._log.error('Hint 2: Maybe the port number does not match.')
            raise CustomError(errorCode, 'errorId:%s errorMessage=%s' % (errorId, errorMessage))
        if errorCode in [509, 10141]:
            # errorCode:509 errorId:-1 errorMessage=Exception caught while reading socket - Broken pipe
            # errorCode=509 errorMessage=Exception caught while reading socket - Connection reset by peer -- Reason: Invoke connectWrapper() when there is connection already.
            # errorCode=509 errorMessage=Exception caught while reading socket - Connection reset by peer -- Reason 1: IB Gateway was turned off suddenly
            # errorCode:10141 errorId:-1 errorMessage=Paper trading disclaimer must first be accepted for API connection.
            # errorCode:509 errorId:-1 errorMessage=Exception caught while reading socket - Connection reset by peer
            # errorCode:509 errorId:-1 errorMessage=Exception caught while reading socket - Function not implemented
            self._log.error(__name__ + '::error: errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorMessage))
            self._log.error('Hint: Restart Trader Workstation(TWS) or IB Gateway and try it again.')
            # self._log.error('Hint: IBridgePy Premium members can turn on the auto-connection feature by settings.py --> PROJECT --> autoReconnectPremium --> True')
            self._log.error('Hint: Please refer to YouTube tutorial https://youtu.be/pson8T5ZaRw')
            raise CustomError(errorCode, 'errorId:%s errorMessage=%s' % (errorId, errorMessage))

        elif errorCode in [1100, 1101, 1102]:
            if errorCode == 1100:
                # Your TWS/IB Gateway has been disconnected from IB servers. This can occur because of an
                # internet connectivity issue, a nightly reset of the IB servers, or a competing session.
                self._connectionGatewayToServer = False
            elif errorCode in [1101, 1102]:
                # 1101
                # The TWS/IB Gateway has successfully reconnected to IB's servers. Your market data requests have
                # been lost and need to be re-submitted.
                # 1102
                # The TWS/IB Gateway has successfully reconnected to IB's servers. Your market data requests have been
                # recovered and there is no need for you to re-submit them.
                self._connectionGatewayToServer = True

        elif errorCode in [2100, 2103, 2104, 2105, 2106, 2107, 2108, 2110, 2119, 2137, 2157, 2158]:
            if errorCode in [2103, 2157]:
                # errorCode=2157 errorMessage=Sec-def data farm connection is broken:secdefnj
                self._connectionMarketDataFarm = False
            elif errorCode in [2104, 2108, 2158]:
                # errorCode=2104 errorMessage=Market data farm connection is OK:usfarm.nj
                # errorCode=2158 errorMessage=Sec-def data farm connection is OK:secdefnj
                # errorCode=2108 errorMessage=Market data farm connection is inactive but should be available upon demand.usfarm.nj
                self._connectionMarketDataFarm = True
            elif errorCode == 2105:
                # 2105 = HMDS dataFromServer farm connection is broken:ushmds
                self._connectionHistDataFarm = False
            elif errorCode in [2106, 2107]:
                # errorCode=2106 errorMessage=HMDS data farm connection is OK:ushmds
                self._connectionHistDataFarm = True
            elif errorCode == 2110:
                # Connectivity between TWS and server is broken. It will be restored automatically.
                # noinspection PyAttributeOutsideInit
                self._connectionGatewayToServer = False
                # noinspection PyAttributeOutsideInit
                self._connectionHistDataFarm = False
                # noinspection PyAttributeOutsideInit
                self._connectionMarketDataFarm = False
            elif errorCode == 2137:
                # errorCode=2137 errorMessage=The closing order quantity is greater than your current position.
                self._log.error(__name__ + '::error: errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorMessage))
                self._log.error('errorCode=2137 is not a critical error in IBridgePy anymore. To hide this error, TWS -> Global Configuration -> Messages -> Cross side warning (untick & save) -> Uncheck it.')
            elif errorCode == 2100:
                # errorCode=2100 errorMessage=API client has been unsubscribed from account data.
                self._activeRequests.set_all_requests_of_a_reqType_to_a_status('reqAccountUpdates', ReqAttr.Status.COMPLETED)
                return
        elif errorCode in [202, 10147, 10148]:
            # 202: cancel order is confirmed
            # 10148, error message: OrderId 230 that needs to be cancelled can not be cancelled, state: Cancelled.
            # 10147, error message: OrderId 2 that needs to be cancelled is not found.
            # errorId is OrderId in this case
            self._activeRequests.set_a_request_of_an_orderId_to_a_status(errorId, ReqAttr.Status.COMPLETED)

        elif errorCode in [201, 399, 2113, 2148, 2109]:  # No action, just show error message
            # 201 = order rejected - Reason: No such order
            # 201 errorMessage=Order rejected - reason:CASH AVAILABLE: 28328.69; CASH NEEDED FOR THIS ORDER AND OTHER PENDING ORDERS: 56477.64
            # 201 Order rejected -
            # 2109: Order Event Warning: Attribute 'Outside Regular Trading Hours' is ignored based on the order type and destination. PlaceOrder is now being processed.
            self._log.error(__name__ + ':errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorMessage))
        elif errorCode in [2176]:  # No action, only debug message
            # 2176: Warning: Your API version does not support fractional share size rules. Please upgrade to a minimum version 163. Trimmed value 256069.05 to 256069. A new error from TWS only 20230112
            self._log.debug(__name__ + ':errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorMessage))
        elif errorCode == 162:
            if 'API scanner subscription cancelled' in errorMessage:
                self._activeRequests.set_a_request_of_a_reqId_to_a_status(errorId, ReqAttr.Status.COMPLETED)
                return  # not a true error
            else:
                if self._activeRequests.has_reqId(errorId):
                    self._log.error(__name__ + ':errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorMessage))
                    self._print_version()
                    raise CustomError(errorCode, 'errorId:%s errorMessage=%s' % (errorId, errorMessage))
                else:
                    return  # the error message is not related to the latest request. Do not handle it anymore. because IB may throw the old error a few times.

        elif 110 <= errorCode <= 449:
            # 404: errorMessage=Order held while securities are located = IB doesn't have available shares to borrow and doesn't let short order.
            if errorCode == 165:
                # 165 = Historical Market Data Service query message:10 out of 178 items retrieve
                return
            self._log.error(__name__ + '::error:errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorMessage))
            if errorCode == 200:
                # 200 = No security definition has been found for the request.

                # A special case.
                # The connectivity is lost during reqHistoricalData.
                # If get 200 at this moment, it is a fake error.
                if (self._connectionGatewayToServer is False) or (self._connectionHistDataFarm is False):
                    self._log.error(__name__ + '::error: <No security definition has been found for the request> might be a false statement because connectivity to IB server is lost.')
                    return

                if errorId in self._allRequests.keys():
                    reqId = errorId
                    if 'contract' in self._allRequests[errorId].param:
                        self._log.error(print_IBCpp_contract(self._allRequests[errorId].param['contract']))
                    else:
                        self._log.error(print_IBCpp_contract(self._allRequests[errorId].param['security']))
                else:
                    reqId = self._activeRequests.find_reqId_by_int_orderId(int(errorId))
                    if reqId:
                        self._log.error(print_IBCpp_contract(self._allRequests[reqId].param['contract']))
                    else:
                        self._log.error(__name__ + '::error: please report this error to IBridgePy@gmail.com for further assistance. Thanks')
                        self._print_version_and_exit()
                # if the reqId is an active request, raise error.
                # Otherwise, ignore error because IB may throw the old error a few times.
                if self._activeRequests.has_reqId(reqId):
                    raise CustomError(errorCode, 'errorId:%s errorMessage=%s' % (errorId, errorMessage))
                else:
                    return

            # elif errorCode == 165:  # Historical Market Data Service query message:Trading TWS session is connected from a different IP address
            self._print_version()
            raise CustomError(errorCode, 'errorId:%s errorMessage=%s' % (errorId, errorMessage))
        elif 994 <= errorCode <= 999 or 972 <= errorCode <= 978:
            self._log.error(__name__ + ':errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorMessage))
            self._log.error('Hint: Please refer to YouTube tutorial https://youtu.be/pson8T5ZaRw')
            self._print_version_and_exit()
        elif 979 <= errorCode <= 988:
            self._log.error(__name__ + ':errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorMessage))
            self._log.error('IBridgePy community version supports backtest on US equities only. Please visit https://ibridgepy.com/features-of-ibridgepy/ and consider IBridgePy Backtester version.')
            self._print_version_and_exit()
        else:
            # errorCode=504 errorMessage=Not connected
            self._log.error(__name__ + '::error: errorId=%s errorCode=%s errorMessage=%s' % (errorId, errorCode, errorMessage))
            self._print_version()
            raise CustomError(errorCode, 'errorId:%s errorMessage=%s' % (errorId, errorMessage))

    def _print_version(self):
        self._log.error(__name__ + '::_print_version:IBridgePy version= %s' % (str(self.versionNumber),))

    def _print_version_and_exit(self):
        self._log.error(__name__ + '::_print_version_and_exit:EXIT IBridgePy version= %s' % (str(self.versionNumber),))
        exit()

    def execDetails(self, reqId, contract, execution):
        """
        !!!!!! reqId is always -1 based on experiences
        :param reqId:
        :param contract:
        :param execution:
        :return:
        """
        self._log.debug(__name__ + '::execDetails: reqId=%s contract=%s execution=%s' % (reqId, print_IBCpp_contract(contract), print_IBCpp_execution(execution)))
        int_orderId = execution.orderId
        ibpyOrderId = self._idConverter.fromIBtoBroker(int_orderId)
        accountCode = execution.acctNumber
        self._singleTrader.set_execDetails(self.brokerName, accountCode,
                                           ExecDetailsRecord(ibpyOrderId, contract, execution))

        # IB will not invoke updateAccountValue immediately after execDetails
        # http://www.ibridgepy.com/knowledge-base/#Q_What_functions_will_be_called_back_from_IB_server_and_what_is_the_sequence_of_call_backs_after_an_order_is_executed
        # To make sure the user know the rough cashValue, IBridgePy has to simulate them.
        # The accurate value will be updated by IB regular updateAccountValue every 3 minutes.
        # The positionValue and portfolioValues are not simulated for live trading because the user just care about cashValue to buy other contracts
        # These values will be updated by IB regular updateAccountValue every 3 minutes.
        currentCashValue = self._singleTrader.get_account_info(self.brokerName, accountCode, 'TotalCashValue')
        cashChange = execution.shares * float(execution.price)
        if execution.side == 'BOT':
            currentCashValue -= cashChange
        elif execution.side == 'SLD':
            currentCashValue += cashChange
        self.updateAccountValue('TotalCashValue', currentCashValue, 'USD', accountCode)

    def historicalData(self, reqId, timeString, price_open, price_high, price_low, price_close, volume, barCount, WAP,
                       hasGaps):
        """
        call back function from IB C++ API
        return the historical data for requested security
        """
        self._log.notset(__name__ + '::historicalData: reqId=%s timeString=%s volume=%s barCount=%s WAP=%s hasGap=%s' % (reqId, timeString, volume, barCount, WAP, hasGaps))

        # for any reason, the reqId is not in the self.activeRequests,
        # just ignore it. because the callback historicalData must come from the previous request.
        if self._activeRequests.is_reqId_within_activeRequests(reqId):
            aRequest = self._activeRequests.get_by_reqId_otherwise_exit(reqId)
        else:
            return

        if 'finished' in str(timeString):
            aRequest.status = ReqAttr.Status.COMPLETED

        else:
            aRequest.status = ReqAttr.Status.STARTED
            # !!! The followings are removed because formatData is forced to 2 in
            # broker_client_factory::BrokerClient::_send_req_to_server after V 5.8.1
            # if aRequest.param['formatDate'] == 1:
            #     if '  ' in timeString:
            #         dateTime = dt.datetime.strptime(timeString, '%Y%m%d  %H:%M:%S')  # change string to datetime
            #     else:
            #         dateTime = dt.datetime.strptime(timeString, '%Y%m%d')  # change string to datetime
            #     dateTime = pytz.timezone('UTC').localize(dateTime)
            # else:  # formatDate is UTC time in seconds, str type
            #     # The format in which the incoming bars' date should be presented. Note that for day bars, only yyyyMMdd format is available.
            #     if len(timeString) > 9:  # return datetime, not date
            #         dateTime = epoch_to_dt(float(timeString))
            #     else:  # return date, not datetime
            #         dateTime = dt.datetime.strptime(timeString, '%Y%m%d')  # change string to datetime
            #     dateTime = int(dt_to_epoch(dateTime))  # change to int type

            # Even if aRequest.param['formatDate'] is forced to 2 (epoch is expected)
            # At some cases, the return is a date, not a datetime, such as 20220422. Assume that it happens because of daily bars.
            try:
                dateTime = dt.datetime.strptime(timeString, '%Y%m%d')  # change string to datetime
                idx = dt_to_epoch(dateTime)
            except ValueError:
                idx = int(float(timeString))
            newRow = pd.DataFrame({'open': price_open, 'high': price_high,
                                   'low': price_low, 'close': price_close,
                                   'volume': volume}, index=[idx])
            aRequest.returnedResult = pd.concat([aRequest.returnedResult, newRow])

    def nextValidId(self, nextId):
        """
        IB API requires an nextId for every order, and this function obtains
        the next valid nextId. This function is called at the initialization
        stage of the program and results are recorded in startingNextValidIdNumber,
        then the nextId is track by the program when placing orders
        """
        self._log.debug(__name__ + '::nextValidId: Id = ' + str(nextId))
        self._nextId.setUuid(nextId)
        self._activeRequests.set_all_requests_of_a_reqType_to_a_status('reqIds', ReqAttr.Status.COMPLETED)

    def heartBeatsEnd(self):
        self._log.notset(__name__ + '::heartBeatsEnd')
        self._activeRequests.set_all_requests_of_a_reqType_to_a_status('reqHeartBeats', ReqAttr.Status.COMPLETED)

    def openOrder(self, int_ibOrderId, contract, order, orderState):
        """
        call back function of IB C++ API which updates the open orders
        """
        self._log.debug(__name__ + '::openOrder: ibOrderId=%i contract=%s order=%s orderState=%s' % (int_ibOrderId, print_IBCpp_contract(contract), print_IBCpp_order(order), print_IBCpp_orderState(orderState)))

        # For IB only:
        # The int_ibOrderId is 0 or -1 if the order is not placed by IB clients
        # Then, create a string value for it using permId
        # IBridgePy will not touch these orders and the created value is not registered in idConverter
        if int_ibOrderId in [-1]:
            str_ibpyOrderId = 'permIDatIB%s' % (order.permId,)
        else:
            str_ibpyOrderId = self._idConverter.fromIBtoBroker(int_ibOrderId)
        self._singleTrader.set_openOrder(self.brokerName, order.account,
                                         OpenOrderRecord(str_ibpyOrderId, contract, order, orderState))

    def openOrderEnd(self):
        self._log.debug(__name__ + '::openOrderEnd')
        self._activeRequests.set_all_requests_of_a_reqType_to_a_status('reqOneOrder', ReqAttr.Status.COMPLETED)
        self._activeRequests.set_all_requests_of_a_reqType_to_a_status('reqAllOpenOrders', ReqAttr.Status.COMPLETED)
        self._activeRequests.set_all_requests_of_a_reqType_to_a_status('reqOpenOrders', ReqAttr.Status.COMPLETED)
        self._activeRequests.set_all_requests_of_a_reqType_to_a_status('reqAutoOpenOrders', ReqAttr.Status.COMPLETED)

    def orderStatus(self, int_orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId,
                    whyHeld):
        """
        call back function of IB C++ API which update status or certain order
        Same order may be called back multiple times with status of 'Filled'
        orderStatus is always called back after openOrder
        """
        self._log.debug(__name__ + '::orderStatus: int_orderId=%s status=%s filled=%s remaining=%s aveFillPrice=%s' % (int_orderId, status, filled, remaining, avgFillPrice))
        str_ibpyOrderId = self._idConverter.fromIBtoBroker(int_orderId)
        reqId = self._activeRequests.find_reqId_by_int_orderId(int_orderId)
        # This orderStatus is called back because of an active request within this session so that reqId is NOT None
        if reqId is not None:
            aRequest = self._activeRequests.get_by_reqId_otherwise_exit(reqId)
            if aRequest.reqType in ['placeOrder', 'modifyOrder']:
                aRequest.returnedResult = str_ibpyOrderId
                aRequest.status = ReqAttr.Status.COMPLETED
        else:  # This orderStatus is called back because of an existing order so that reqId is None
            # DO NOT DELETE
            # For Debug only
            # print(__name__ + '::orderStatus: cannot find reqId by int_orderid=%s' % (int_orderId,))
            # print(self._idConverter.fromIBToBrokerDict)
            # print(self._idConverter.fromBrokerToIBDict)
            # print(self.activeRequests)
            pass

        accountCode = self._singleTrader.get_accountCode_by_ibpyOrderId(self.brokerName, str_ibpyOrderId)
        self._singleTrader.set_orderStatus(self.brokerName,
                                           accountCode,
                                           OrderStatusRecord(str_ibpyOrderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld))

    def position(self, accountCode, contract, amount, cost_basis):
        """
        call back function of IB C++ API which updates the position of a security
        of a account
        """
        self._log.debug(__name__ + '::position: accountCode=%s contract=%s amount=%s cost_basis=%s' % (accountCode, print_IBCpp_contract(contract), amount, cost_basis))
        # Conclusion: called-back position contract may or may not have exchange info,
        # never see primaryExchange.
        # STK has exchange, CASH does not, FUT does not
        # if contract.exchange != '':
        #    self._log.error(__name__ + '::position: EXIT, contract has exchange=%s' % (print_contract(contract),))
        #    exit()
        security = stripe_exchange_primaryExchange_from_contract(contract)
        self._singleTrader.set_position(self.brokerName, accountCode,
                                        PositionRecord(security.full_print(), amount, cost_basis, contract))

    def positionEnd(self):
        self._log.debug(__name__ + '::positionEnd: all positions recorded')
        self._activeRequests.set_all_requests_of_a_reqType_to_a_status('reqPositions', ReqAttr.Status.COMPLETED)

    def realtimeBar(self, reqId, aTime, price_open, price_high, price_low, price_close, volume, wap, count):
        """
        call back function from IB C++ API
        return realTimeBars for requested security every 5 seconds
        """
        self._log.notset(__name__ + '::realtimeBar: reqId=%s time=%s price_open=%s price_high=%s price_low=%s price_close=%s volume=%s wap=%s count=%s' % (reqId, aTime, price_open, price_high, price_low, price_close, volume, wap, count))

    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, projection, legsStr):
        self._log.debug(__name__ + '::scannerData: reqId=%s rank=%s contractDetails.summary%s distance=%s benchmark=%s project=%s legsStr=%s' % (reqId, rank, print_IBCpp_contract(contractDetails.summary), distance, benchmark, projection, legsStr))
        aRequest = self._activeRequests.get_by_reqId_otherwise_exit(reqId)
        security = from_contract_to_security(contractDetails.summary)
        newRow = pd.DataFrame({'rank': rank,
                               # 'contractDetails': contractDetails,
                               'security': security,
                               # 'distance': distance,
                               # 'benchmark': benchmark,
                               # 'projection': projection,
                               # 'legsStr': legsStr
                               }, index=[len(aRequest.returnedResult)])
        aRequest.returnedResult = aRequest.returnedResult.append(newRow)

    def scannerDataEnd(self, reqId):
        self._log.debug(__name__ + '::scannerDataEnd:' + str(reqId))
        self._activeRequests.set_a_request_of_a_reqId_to_a_status(reqId, ReqAttr.Status.COMPLETED)

    def scannerParameters(self, xml):
        self._log.debug(__name__ + '::scannerParameters:')
        self._activeRequests.set_all_requests_of_a_reqType_to_a_status_and_set_result('reqScannerParameters',
                                                                                      ReqAttr.Status.COMPLETED, xml)

    def tickGeneric(self, reqId, field, value):
        self._log.notset(__name__ + '::tickGeneric: reqId=%i field=%s value=%d' % (reqId, field, value))

    def tickOptionComputation(self, reqId, tickType, impliedVol, delta, optPrice, pvDividend, gamma, vega, theta, undPrice):
        self._log.debug(__name__ + '::tickOptionComputation:reqId=%s %s %s %s %s %s %s %s %s %s' % (reqId, tickType, impliedVol, delta, optPrice, pvDividend, gamma, vega, theta, undPrice))
        str_security = self._allRequests[reqId].param['security'].full_print()
        # For any reason, the reqId is not in the self.activeRequests, just update the price, not need to be an active request at all.
        self._dataFromServer.set_tickInfoRecord(TickOptionComputationRecord(str_security, tickType, impliedVol, delta, optPrice, pvDividend, gamma, vega, theta, undPrice))

    def tickPrice(self, reqId, tickType, price, canAutoExecute):
        """
        call back function of IB C++ API. This function will get tick prices
        """
        self._log.notset(__name__ + '::tickPrice:reqId=%s tickType=%s price=%s' % (reqId, tickType, price))

        # If it is an active request, needs to update request.status
        # In order to guarantee valid ask and bid prices, it needs to check if both of ask price and bid price
        # is received.
        if self._activeRequests.is_reqId_within_activeRequests(reqId):
            aRequest = self._activeRequests.get_by_reqId_otherwise_exit(reqId)
            if aRequest.status != ReqAttr.Status.COMPLETED:
                if tickType == 1:
                    if 'Bid' not in aRequest.status:
                        aRequest.status += 'Bid'
                elif tickType == 2:
                    if 'Ask' not in aRequest.status:
                        aRequest.status += 'Ask'
                if 'Ask' in aRequest.status and 'Bid' in aRequest.status:
                    aRequest.status = ReqAttr.Status.COMPLETED

        # For any reason, the reqId is not in the self.activeRequests, just update the price, not need to be an active request at all.
        str_security = self._allRequests[reqId].param['security'].full_print()
        timestamp = self._timeGenerator.get_current_time()
        self._dataFromServer.set_tickInfoRecord(TickPriceRecord(str_security, tickType, price, canAutoExecute, timestamp))

    def tickSize(self, reqId, tickType, size):
        """
        call back function of IB C++ API. This function will get tick size
        """
        self._log.notset(__name__ + '::tickSize: reqId=%s tickType=%s size=%s' % (reqId, MSG_TABLE[tickType], size))

        # For any reason, the reqId is not in the self.activeRequests, just update the price, not need to be an active request at all.
        str_security = self._allRequests[reqId].param['security'].full_print()
        self._dataFromServer.set_tickInfoRecord(TickSizeRecord(str_security, tickType, size))

    def tickSnapshotEnd(self, reqId):
        self._log.notset(__name__ + '::tickSnapshotEnd: ' + str(reqId))

    def tickString(self, reqId, field, value):
        """
        IB C++ API call back function. The value variable contains the last
        trade price and volume information. User show define in this function
        how the last trade price and volume should be saved
        RT_volume: 0 = trade timestamp; 1 = price_last,
        2 = size_last; 3 = record_timestamp
        """
        self._log.notset(__name__ + '::tickString: reqId=%s field=%s value=%s' % (reqId, field, value))
        # For any reason, the reqId is not in the self.activeRequests, just update the price, not need to be an active request at all.
        str_security = self._allRequests[reqId].param['security'].full_print()
        self._dataFromServer.set_tickInfoRecord(TickStringRecord(str_security, field, value))

    def updateAccountTime(self, tm):
        self._log.notset(__name__ + '::updateAccountTime:' + str(tm))

    def updateAccountValue(self, key, value, currency, accountCode):
        """
        IB callback function
        update account values such as cash, PNL, etc
        !!!!!!!! type(value) is STRING !!!!!!!!
        """
        self._log.notset(__name__ + '::updateAccountValue: key=%s value=%s currency=%s accountCode=%s _singleTrader=%s' % (key, value, currency, accountCode, id(self._singleTrader)))
        try:
            value = float(value)
        except ValueError:
            # IB will callback some many account info. All of them are string
            # However, the concept of some of these values are float. So, convert them to float if possible. Otherwise, keep them as string
            pass
        self._singleTrader.set_updateAccountValue(self.brokerName, accountCode,
                                                  UpdateAccountValueRecord(key, value, currency, accountCode))

    def updatePortfolio(self, contract, amount, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL,
                        accountCode):
        self._log.notset(
            __name__ + '::updatePortfolio: contract=%s amount=%s marketPrice=%s marketValue=%s averageCost=%s unrealizedPNL=%s realizedPNL=%s accountCode=%s'
            % (str(contract), str(amount), str(marketPrice), str(marketValue), str(averageCost), str(unrealizedPNL),
               str(realizedPNL), str(accountCode)))

        # Because IB does not callback position and updateAccountValues,
        # it needs to make fake calls to make sure the account info is correct
        # It is not correct, it will be fixed by the real call-backs
        self.position(accountCode, contract, amount, averageCost)
