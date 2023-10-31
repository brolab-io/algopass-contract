import * as algokit from '@algorandfoundation/algokit-utils'
import { AlgopassClient } from '../artifacts/algopass/client'

// Below is a showcase of various deployment options you can use in TypeScript Client
export async function deploy() {
  console.log('=== Deploying Algopass ===')

  const algod = algokit.getAlgoClient(algokit.getAlgoNodeConfig('testnet', 'algod'))
  const indexer = algokit.getAlgoIndexerClient(algokit.getAlgoNodeConfig('testnet', 'indexer'))
  const deployer = await algokit.mnemonicAccountFromEnvironment({ name: 'DEPLOYER', fundWith: algokit.algos(3) }, algod)
  // const deployer = await algokit.mnemonicAccount(process.env.ACCOUNT_MNEMONIC!)
  await algokit.ensureFunded(
    {
      accountToFund: deployer,
      minSpendingBalance: algokit.algos(2),
      minFundingIncrement: algokit.algos(2),
    },
    algod,
  )
  const appClient = new AlgopassClient(
    {
      resolveBy: 'creatorAndName',
      findExistingUsing: indexer,
      sender: deployer,
      creatorAddress: deployer.addr,
    },
    algod,
  )
  const isMainNet = await algokit.isMainNet(algod)
  const app = await appClient.deploy({
    allowDelete: !isMainNet,
    allowUpdate: !isMainNet,
    onSchemaBreak: isMainNet ? 'append' : 'replace',
    onUpdate: isMainNet ? 'append' : 'update',
  })


  // If app was just created fund the app account
  if (['create', 'replace'].includes(app.operationPerformed)) {
    algokit.transferAlgos(
      {
        amount: algokit.algos(1),
        from: deployer,
        to: app.appAddress,
      },
      algod,
    )
  }

  const method = 'hello'
  const response = await appClient.hello({ name: 'world' })
  console.log(`Called ${method} on ${app.name} (${app.appId}) with name = world, received: ${response.return}`)
}
