import beaker
import pyteal as pt

# from algokit_utils import DELETABLE_TEMPLATE_NAME, UPDATABLE_TEMPLATE_NAME
from beaker.lib.storage import BoxMapping


class UserRecord(pt.abi.NamedTuple):
    name: pt.abi.Field[pt.abi.String]
    bio: pt.abi.Field[pt.abi.String]


class AppState:
    g_counter = beaker.GlobalStateValue(
        stack_type=pt.TealType.uint64, default=pt.Int(0), descr="For user counter"
    )
    g_fee = beaker.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(1000000),
        descr="Fee to create profile",
    )
    b_info = BoxMapping(
        key_type=pt.abi.Address,
        value_type=UserRecord,
        # prefix=pt.Bytes("i")
    )


state = AppState()

app = beaker.Application("algopass", state=state).apply(
    beaker.unconditional_create_approval, initialize_global_state=True
)


@app.external
def init_profile(payment: pt.abi.PaymentTransaction, *, output: pt.abi.Bool) -> pt.Expr:
    return pt.Seq(
        pt.Assert(
            pt.Not(state.b_info[pt.Txn.sender()].exists()), comment="Initialized"
        ),
        pt.Assert(
            payment.get().receiver() == pt.Global.current_application_address(),
            comment="Wrong receiver",
        ),
        pt.Assert(
            payment.get().amount() == state.g_fee.get(),
            comment=f"payment must be for >= {state.g_fee.get()}",
        ),
        state.g_counter.increment(),
        (name := pt.abi.String()).set(pt.Bytes("name")),
        (bio := pt.abi.String()).set(pt.Bytes("bio")),
        (temp := UserRecord()).set(name, bio),
        state.b_info[pt.Txn.sender()].set(temp),
        output.set(pt.Int(1)),
    )


@app.external
def update_profile(
    name: pt.abi.String, bio: pt.abi.String, *, output: UserRecord
) -> pt.Expr:
    return pt.Seq(
        pt.Assert(state.b_info[pt.Txn.sender()].exists(), comment="Not Exist"),
        (cur_p := UserRecord()).decode(state.b_info[pt.Txn.sender()].get()),
        # (name := pt.abi.String()).set(pt.Bytes("name")),
        # (bio := pt.abi.String()).set(pt.Bytes("bio")),
        cur_p.set(name, bio),
        state.b_info[pt.Txn.sender()].set(cur_p),
        output.decode(cur_p.encode()),
    )


# @app.update(authorize=beaker.Authorize.only_creator(), bare=True)
# def update() -> pt.Expr:
#     return pt.Assert(
#         pt.Tmpl.Int(UPDATABLE_TEMPLATE_NAME),
#         comment="Check app is updatable",
#     )


# @app.delete(authorize=beaker.Authorize.only_creator(), bare=True)
# def delete() -> pt.Expr:
#     return pt.Assert(
#         pt.Tmpl.Int(DELETABLE_TEMPLATE_NAME),
#         comment="Check app is deletable",
#     )


@app.external
def hello(name: pt.abi.String, *, output: pt.abi.String) -> pt.Expr:
    return output.set(pt.Concat(pt.Bytes("Hello, "), name.get()))
