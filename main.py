from dotenv import load_dotenv
from web3 import Web3
import os
import json

# Load ABI
with open("abi.json", "r") as f:
    abi = json.load(f)

load_dotenv()
# Connect to Ethereum node
node_url = os.getenv("RPC")
web3 = Web3(Web3.HTTPProvider(node_url))

# Check connection
if not web3.is_connected():
    print("Failed to connect to the Ethereum node.")
    exit()

# Define contracts and roles
contracts_info = {
    "EthenaMinting": {  # EthenaMinting
        "deployment_block": 18571427,
        "roles": [
            "DEFAULT_ADMIN_ROLE",
            "MINTER_ROLE",
            "REDEEMER_ROLE",
            "GATEKEEPER_ROLE",
            "COLLATERAL_MANAGER_ROLE",
        ],
        "address": "0x2CC440b721d2CaFd6D64908D6d8C4aCC57F8Afc3",
    },
    "StakedUSDeV2": {
        "deployment_block": 18571359,
        "roles": [
            "DEFAULT_ADMIN_ROLE",
            "REWARDER_ROLE",
            "BLACKLIST_MANAGER_ROLE",
            "SOFT_RESTRICTED_STAKER_ROLE",
            "FULL_RESTRICTED_STAKER_ROLE",
        ],
        "address": "0x9D39A5DE30e57443BfF2A8307A4256c8797A3497",
    },
    # Add more contracts and roles as needed
}


# Function to convert role name to bytes32
def role_to_bytes32(role_name):
    return Web3.keccak(text=role_name).hex()


# Function to scan logs for role changes
def scan_role_changes(contract_name, contract_address, from_block, roles):
    contract = web3.eth.contract(address=contract_address, abi=abi)

    # Define event signatures
    role_granted_topic = Web3.keccak(text="RoleGranted(bytes32,address,address)").hex()
    role_revoked_topic = Web3.keccak(text="RoleRevoked(bytes32,address,address)").hex()

    # Process each role
    for role in roles:
        role_bytes32 = role_to_bytes32(role)

        # Filter for logs with this role
        logs = web3.eth.get_logs(
            {
                "fromBlock": from_block,
                "address": contract_address,
                "topics": [
                    [role_granted_topic, role_revoked_topic],
                    [role_bytes32],
                ],
            }
        )

        # Process logs
        for log in logs:
            if log['topics'][0].hex() == role_granted_topic:
              grant_event = contract.events.RoleGranted().process_receipt({"logs": [log]})
              if grant_event:
                  _, user, admin = (
                      grant_event[0]["args"]["role"],
                      grant_event[0]["args"]["account"],
                      grant_event[0]["args"]["sender"],
                  )
                  print(f"Role {role} granted to {user} by {admin} for {contract_name}")
            else:
              revoke_event = contract.events.RoleRevoked().process_receipt(
                  {"logs": [log]}
              )
              if revoke_event:
                  role, user, admin = (
                      revoke_event[0]["args"]["role"],
                      revoke_event[0]["args"]["account"],
                      revoke_event[0]["args"]["sender"],
                  )
                  print("Role %s revoked from %s for %s", role, user, contract_name)


# Process each contract
for contract_name, info in contracts_info.items():
    scan_role_changes(
        contract_name, info["address"], info["deployment_block"], info["roles"]
    )
