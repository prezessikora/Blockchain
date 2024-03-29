# Module 2 - Create Cryptocurrency

import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Part 1 - Building Blockchain

DIFFICULTY = '00000'

class Blockchain:
    
    
    def __init__(self):
        self.chain = [];
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0');
        self.nodes = set()
        
    def check_leading_zeros(self, hash_operation):
        return (hash_operation[:len(DIFFICULTY)] == DIFFICULTY)
    
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain)+1, 
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions}
        self.transactions = []
        self.chain.append(block);
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1;
        check_proof = False;
        
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest();
            if (self.check_leading_zeros(hash_operation) == True):
                print(hash_operation)
                return new_proof;
            else:
                new_proof += 1;    
        
        
        
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode();
        return hashlib.sha256(encoded_block).hexdigest();
    
    def is_chain_valid(self, chain):
        i = len(chain)-1;    

        while i > 0:
            nxt = chain[i]
            prv = chain[i-1]
            
            if (nxt['previous_hash'] != self.hash(prv)):
                return False;
            
            previous_proof = prv['proof'];
            proof = nxt['proof'];            
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            
            if (self.check_leading_zeros(hash_operation)):
                return True;
            
            i = i -1
        
        return True;
      
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount})
        return self.get_previous_block()['index'] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address);
        self.nodes.add(parsed_url.netloc)
    
    
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_lenght = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_lenght and self.is_chain_valid(chain):
                    max_lenght = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
    
# Part 2 - Mining Blockchain

# Create Web App
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False


# Create an address for the node on Port 5000

node_address = str(uuid4()).replace('-', '');

# Create Blockchain
blockchain = Blockchain()

@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block() 
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address, receiver= 'Hugo', amount = 1)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'You just mined a block!',                
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    
    return jsonify(response), 200
    

@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain),
                'open_transactions': blockchain.transactions}
    return jsonify(response), 200

@app.route('/is_valid', methods=['GET'])
def is_valid():
    check = blockchain.is_chain_valid(blockchain.chain);
    response = {'length': len(blockchain.chain), 'valid': check}
    return jsonify(response), 200

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if request.is_json:
        transaction = request.get_json(force=True, silent=True, cache=False)
        transaction_keys = ['sender','receiver','amount']
        print(transaction)
        print(request.data)
        if not all (key in transaction for key in transaction_keys):
            response = {'message': 'Missing transaction keys.'}
            return jsonify(response), 400 
        index = blockchain.add_transaction(transaction['sender'], transaction['receiver'], transaction['amount']);
        response = {'message': f'Transaction will be added to block {index}.'}
        return jsonify(response), 201
    else:
        response = {'message': 'Expecting JSON input.'}
        return jsonify(response), 400 
    
    
# Connecting new nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():    
    json = request.get_json(force=True, silent=True, cache=False)
    nodes = json.get('nodes')
    if nodes is None:
        return "No nodes", 400
    for node in nodes:            
        blockchain.add_node(node)
    response = {'message': 'All the nodes are now connected.',
                'total_nodes' : len(blockchain.nodes)}
    return jsonify(response), 201

@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:        
        response = {'message': 'The chain was replaced.', 
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good the chain is the longest one.',
                    'current_chain': blockchain.chain}

    return jsonify(response), 200


# Run the local node
    
app.run(host='0.0.0.0', port = 5003)