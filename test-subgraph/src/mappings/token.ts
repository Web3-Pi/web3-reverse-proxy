import { BigInt, Bytes, ethereum } from '@graphprotocol/graph-ts'

import { Transfer } from '../types/LINK/ERC20'

import { Account, TransferEvent } from '../types/schema'


const GENESIS_ADDRESS = '0x0000000000000000000000000000000000000000'

export function handleTransfer(event: Transfer): void {
  let amount = event.params.value

  let transferEvent = new TransferEvent(event.transaction.hash.toHex() + '-' + event.logIndex.toString())
  transferEvent.amount = amount
  transferEvent.sender = getOrCreateAccount(event.transaction.from).id

  transferEvent.block = event.block.number
  transferEvent.timestamp = event.block.timestamp
  transferEvent.transaction = event.transaction.hash

  if (event.params.from.toHex() != GENESIS_ADDRESS) {
    let sourceAccount = getOrCreateAccount(event.params.from)
    sourceAccount.balance = sourceAccount.balance.minus(amount)
    sourceAccount.save()
    transferEvent.source = sourceAccount.id
  }

  if (event.params.to.toHex() != GENESIS_ADDRESS) {
    let destinationAccount = getOrCreateAccount(event.params.to)
    destinationAccount.balance = destinationAccount.balance.plus(amount)
    destinationAccount.save()
    transferEvent.destination = destinationAccount.id
  }

  transferEvent.save()
}

function getOrCreateAccount(
  accountAddress: Bytes,
): Account {
  let accountId = accountAddress.toHex()
  let account = Account.load(accountId)

  if (account == null) {
    account = new Account(accountId)
    account.address = accountAddress
    account.balance = BigInt.fromI32(0)
    account.save();
  }

  return account as Account;
}

