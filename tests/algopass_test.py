import pytest
from algokit_utils import (
    ApplicationClient,
    ApplicationSpecification,
    EnsureBalanceParameters,
    OnCompleteCallParametersDict,
    ensure_funded,
    get_localnet_default_account,
)
from algosdk import transaction
from algosdk.atomic_transaction_composer import (
    TransactionWithSigner,
)
from algosdk.encoding import decode_address
from algosdk.v2client.algod import AlgodClient

from smart_contracts.algopass import contract as algopass_contract


@pytest.fixture(scope="session")
def algopass_app_spec(algod_client: AlgodClient) -> ApplicationSpecification:
    return algopass_contract.app.build(algod_client)


@pytest.fixture(scope="session")
def algopass_client(
    algod_client: AlgodClient, algopass_app_spec: ApplicationSpecification
) -> ApplicationClient:
    client = ApplicationClient(
        algod_client,
        app_spec=algopass_app_spec,
        signer=get_localnet_default_account(algod_client),
        template_values={"UPDATABLE": 1, "DELETABLE": 1},
    )
    client.create()
    ensure_funded(
        algod_client,
        EnsureBalanceParameters(
            account_to_fund=client.app_address,
            funding_source=get_localnet_default_account(algod_client),
            min_spending_balance_micro_algos=2000000,
            min_funding_increment_micro_algos=2000000,
        ),
    )

    return client


def test_init_profile(algopass_client: ApplicationClient) -> None:
    acct = get_localnet_default_account(algopass_client.algod_client)
    boxes = [(algopass_client.app_id, decode_address(acct.address))]
    sp = algopass_client.algod_client.suggested_params()
    sp.fee = sp.min_fee * 2
    pay_txn = TransactionWithSigner(
        txn=transaction.PaymentTxn(
            sender=acct.address,
            receiver=algopass_client.app_address,
            amt=1_000_000,
            sp=sp,
        ),
        signer=acct.signer,
    )

    result = algopass_client.call(
        algopass_contract.init_profile,
        transaction_parameters=OnCompleteCallParametersDict(boxes=boxes),
        payment=pay_txn,
    )
    g_counter = algopass_client.get_global_state().get("g_counter")
    assert g_counter == 1
    assert result.return_value == 1


def test_update_profile(algopass_client: ApplicationClient) -> None:
    acct = get_localnet_default_account(algopass_client.algod_client)
    boxes = [(algopass_client.app_id, decode_address(acct.address))]
    result = algopass_client.call(
        algopass_contract.update_profile,
        transaction_parameters=OnCompleteCallParametersDict(boxes=boxes),
        name="Leo Pham",
        bio="Leo Pham is a blockchain developer",
    )

    assert result.return_value == ["Leo Pham", "Leo Pham is a blockchain developer"]


def test_says_hello(algopass_client: ApplicationClient) -> None:
    result = algopass_client.call(algopass_contract.hello, name="World")

    assert result.return_value == "Hello, World"
