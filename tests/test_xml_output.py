from sepacbi import SctFactory, Invoice, DebitNote, Text #Payment,
from .definitions import *
import re
import sys
from datetime import datetime, date

from lxml import etree

Payment = SctFactory.get_payment()

PYTHON3 = False
if sys.version_info[0] >= 3:
    PYTHON3 = True


TIMESTAMP_RE = re.compile(r'<CreDtTm>[-0-9:.T]+</CreDtTm>')
CANONICAL_TIMESTAMP = '<CreDtTm>' + datetime.now().isoformat() + '</CreDtTm>'


def canonicalize_xml(xmlstring):
    """
    Wipe out the info that cannot be constant in the XML string (such as
    autogenerated timestamps), parse it and and reoutput it.
    """
    if PYTHON3:
        if hasattr(xmlstring, 'decode'):
            xmlstring = xmlstring.decode(encoding='utf-8')
    string = TIMESTAMP_RE.sub(CANONICAL_TIMESTAMP, xmlstring)
    tree = etree.fromstring(string)
    return etree.tostring(tree, pretty_print=True)


def compare_xml(tree, filename, save=False):
    """
    Compare a generated XML tree with the content of a specific file.
    """
    from os.path import dirname, join
    full_path = join(dirname(__file__), filename)
    tree = canonicalize_xml(tree)
    if save:
        open(full_path, 'w').write(tree)
        raise Exception('saved!')
    file_content = canonicalize_xml(open(full_path, 'r').read())
    assert tree == file_content


def test_payment_basic():
    payment = Payment(debtor=biz_with_cuc, account=acct_37, req_id='StaticId',
                      execution_date=date(2014, 5, 15))
    payment.add_transaction(amount=198.25, account=acct_86, creditor=beta,
                            rmtinfo='Causale 1')
    compare_xml(payment.xml_text(), 'payment_basic.xml')


def test_payment_multitrans():
    payment = Payment(debtor=biz_with_cuc, account=acct_37, req_id='StaticId',
                      execution_date=date(2014, 5, 15))
    payment.add_transaction(amount=198.25, account=acct_86, creditor=beta,
                            rmtinfo='Causale 1')
    payment.add_transaction(amount=350.00, account=acct_37,
                            creditor=biz_with_cuc,
                            rmtinfo='Altra causale')
    payment.add_transaction(amount=9532.21, account=foreign_acct,
                            bic='ABCDESNN', creditor=alpha,
                            docs=[Invoice(18512, 4500),
                                  DebitNote(1048, 5032.21,
                                            date(1995, 4, 21))])
    payment.add_transaction(
        amount=1242.80, creditor=pvt, account=acct_86,
        category='SALA', rmtinfo='Salary')

    compare_xml(payment.xml_text(), 'payment_multitrans.xml')


def test_payment_misc_features():
    payment = Payment(
        debtor=biz, account=acct_37, req_id='StaticId',
        execution_date=date(2014, 5, 15),
        ultimate_debtor=beta, charges_account=acct_86, envelope=True,
        initiator=biz_with_cuc, batch=True, high_priority=True)
    payment.add_transaction(amount=198.25, account=acct_86, creditor=beta,
                            rmtinfo='Causale 1')
    compare_xml(payment.xml_text(), 'payment_misc_1.xml')

    payment.high_priority = False
    payment.add_transaction(amount=350.00, account=acct_37,
                            creditor=biz_with_cuc,
                            rmtinfo='Altra causale')
    payment.add_transaction(amount=9532.21, account=foreign_acct,
                            bic='ABCDESNN', creditor=alpha,
                            docs=[Invoice(18512, 4500),
                                  DebitNote(1048, 5032.21,
                                            date(1995, 4, 21))])
    payment.add_transaction(
        amount=1242.80, creditor=pvt, account=acct_86,
        category='SALA', docs=[Text('Salary payment')])

    compare_xml(payment.xml_text(), 'payment_misc_2.xml')
