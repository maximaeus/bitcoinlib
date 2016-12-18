# -*- coding: utf-8 -*-
#
#    bitcoinlib db.py
#    © 2016 November - 1200 Web Development <http://1200wd.com/>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import csv
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Float, String, Boolean, Sequence, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


DEFAULT_DATABASEDIR = os.path.join(os.path.dirname(__file__), 'data/')
DEFAULT_DATABASEFILE = 'bitcoinlib.sqlite'
DEFAULT_DATABASE = DEFAULT_DATABASEDIR + DEFAULT_DATABASEFILE

Base = declarative_base()


class DbInit:

    def __init__(self, databasefile=DEFAULT_DATABASE):
        engine = create_engine('sqlite:///%s' % databasefile)
        Session = sessionmaker(bind=engine)

        if not os.path.exists(databasefile):
            if not os.path.exists(DEFAULT_DATABASEDIR):
                os.makedirs(DEFAULT_DATABASEDIR)
            Base.metadata.create_all(engine)
            self._import_config_data(Session)

        self.session = Session()

    @staticmethod
    def _import_config_data(ses):
        for fn in os.listdir(DEFAULT_DATABASEDIR):
            if fn.endswith(".csv"):
                with open('%s%s' % (DEFAULT_DATABASEDIR, fn), 'r') as csvfile:
                    session = ses()
                    tablename = fn.split('.')[0]
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        if tablename == 'providers':
                            session.add(DbProvider(**row))
                        elif tablename == 'networks':
                            session.add(DbNetwork(**row))
                        else:
                            raise ImportError(
                                "Unrecognised table '%s', please update import mapping or remove file" % tablename)
                    session.commit()
                    session.close()


class DbWallet(Base):
    __tablename__ = 'wallets'
    id = Column(Integer, Sequence('wallet_id_seq'), primary_key=True)
    name = Column(String(50), unique=True)
    owner = Column(String(50))
    network_name = Column(String, ForeignKey('networks.name'))
    network = relationship("DbNetwork")
    purpose = Column(Integer, default=44)
    main_key_id = Column(Integer)
    keys = relationship("DbKey", back_populates="wallet")
    balance = Column(Float, default=0)


class DbKey(Base):
    __tablename__ = 'keys'
    id = Column(Integer, Sequence('key_id_seq'), primary_key=True)
    parent_id = Column(Integer, Sequence('parent_id_seq'))
    name = Column(String(50))
    account_id = Column(Integer)
    depth = Column(Integer)
    change = Column(Integer)  # TODO: 0 or 1 (0=external receiving address, 1=internal change addresses)
    address_index = Column(Integer)  # TODO: constraint gap no longer than 20
    key = Column(String(255), unique=True)
    key_wif = Column(String(255), unique=True)
    address = Column(String(255), unique=True)
    purpose = Column(Integer, default=44)
    is_private = Column(Boolean)
    path = Column(String(100))
    wallet_id = Column(Integer, ForeignKey('wallets.id'))
    wallet = relationship("DbWallet", back_populates="keys")
    utxos = relationship("DbUtxo", back_populates="key")
    balance = Column(Float, default=0)


class DbNetwork(Base):
    __tablename__ = 'networks'
    name = Column(String(20), unique=True, primary_key=True)
    description = Column(String(50))


class DbProvider(Base):
    __tablename__ = 'providers'
    name = Column(String(50), primary_key=True, unique=True)
    provider = Column(String(50))
    network_name = Column(String, ForeignKey('networks.name'))
    network = relationship("DbNetwork")
    base_url = Column(String(100))
    api_key = Column(String(100))


class DbTransaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, Sequence('transaction_id_seq'), primary_key=True)
    transaction_id = Column(String(50), unique=True)


# BLOCKEXPLORER
# {
#   "address": "n2PuaAguxZqLddRbTnAoAuwKYgN2w2hZk7",
#   "txid": "dbfdc2a0d22a8282c4e7be0452d595695f3a39173bed4f48e590877382b112fc",
#   "vout": 0,
#   "ts": 1401276201,
#   "scriptPubKey": "76a914e50575162795cd77366fb80d728e3216bd52deac88ac",
#   "amount": 0.001,
#   "confirmations": 3
# },
#
# BLOCKR.IO
# {"address": "n3UKaXBRDhTVpkvgRH7eARZFsYE989bHjw",
#  "unspent": [
#      {"tx": "d3c7fbd3a4ca1cca789560348a86facb3bb21dcd75ed38e85235fb6a32802955",
#       "amount": "0.00890000",
#       "n": 1,
#       "confirmations": 46949,
#       "script": "76a914f0d34949650af161e7cb3f0325a1a8833075165088ac"}],
#  "with_multisigs": True},
#
# BLOCKCHAIN.INFO
#     "unspent_outputs":[
#         {
#             "tx_age":"1322659106",
#             "tx_hash":"e6452a2cb71aa864aaa959e647e7a4726a22e640560f199f79b56b5502114c37",
#             "tx_index":"12790219",
#             "tx_output_n":"0",
#             "script":"76a914641ad5051edd97029a003fe9efb29359fcee409d88ac", (Hex encoded)
#             "value":"5000661330"
#         }
#     ]

class DbUtxo(Base):
    __tablename__ = 'utxos'
    id = Column(Integer, Sequence('utxo_id_seq'), primary_key=True)
    key_id = Column(Integer, ForeignKey('keys.id'))
    key = relationship("DbKey", back_populates="utxos")
    tx_hash = Column(String(64), unique=True)
    confirmations = Column(Integer)
    output_n = Column(Integer)
    index = Column(Integer)
    value = Column(Float)
    script = Column(String)


if __name__ == '__main__':
    DbInit()