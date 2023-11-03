import * as algokit from '@algorandfoundation/algokit-utils'
import { AlgopassClient } from '../artifacts/algopass/client'
import algosdk, { decodeAddress } from 'algosdk'
import { getAlgoNodeConfig } from '@algorandfoundation/algokit-utils'

// Below is a showcase of various deployment options you can use in TypeScript Client
export async function deploy() {
  console.log('=== Deploying Algopass ===')

  const algod = algokit.getAlgoClient(getAlgoNodeConfig('testnet', 'algod'))
  const indexer = algokit.getAlgoIndexerClient(getAlgoNodeConfig('testnet', 'indexer'))
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
        amount: algokit.algos(0.5),
        from: deployer,
        to: app.appAddress,
      },
      algod,
    )
  }

  const method = 'hello'
  const response = await appClient.hello({ name: 'world' })
  console.log(`Called ${method} on ${app.name} (${app.appId}) with name = world, received: ${response.return}`)
  const boxes = [{ appId: app.appId, name: decodeAddress(deployer.addr).publicKey }]


  try {
    const resultGetProfile = await appClient.getProfile({ user: deployer.addr }, {
      boxes,
    })
    console.log(resultGetProfile.return)

    const resultUpdate = await appClient.updateProfile({
      name: "John Doe",
      bio: "I am a developer",
      uri: "https://www.linkedin.com/in/john-doe",
      urls: [
        ["github", "hongthaipham"],
        ["twitter", "hongthaipham"],
        ["linkedin", "hongthaipham"],
        ["email", "hongthaipro@gmail.com"]
      ]
    }, { boxes })

    console.log(`Called updateProfile on ${app.name} (${app.appId}) with user = ${deployer.addr}`)
    console.log(resultUpdate.return)

  } catch (error) {
    const suggestedParams = await algod.getTransactionParams().do();
    const ptxn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
      from: deployer.addr,
      suggestedParams,
      to: app.appAddress,
      amount: 1_000_000,
    });

    const resultInit = await appClient.initProfile({ payment: ptxn, urls: [["email", ""]] }, { boxes })
    console.log(`Called initProfile on ${app.name} (${app.appId}) with user = ${deployer.addr}, received: ${resultInit.return}`)
    console.log(error.message)
  }




}
