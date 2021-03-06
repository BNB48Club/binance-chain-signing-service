from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException

from binance_chain.messages import NewOrderMsg

from config.config import WalletConfig, UserSettings
from api.models.schema import SignOrderSchema
from api.constants.constants import WalletPermission
from api.utils.wallet import get_wallet, increment_wallet_sequence
from api.security.auth import get_current_user, user_has_wallet_permission

router = APIRouter()


@router.post("/order/sign")
async def sign_order(
    signed_order: SignOrderSchema,
    req_wallet: WalletConfig = Depends(get_wallet),
    current_user: UserSettings = Depends(get_current_user)
):
    """Sign a new order message, returning the hex data

    """
    if not req_wallet.has_permission(WalletPermission.TRADE):
        raise HTTPException(status_code=403, detail=f"No permission {WalletPermission.TRADE}")

    # check user has permission for this wallet
    if not user_has_wallet_permission(current_user, signed_order.wallet_name, WalletPermission.TRADE):
        raise HTTPException(
            status_code=403,
            detail=f"User has no permission {WalletPermission.TRADE} on wallet {signed_order.wallet_name}"
        )

    # create the message
    msg = NewOrderMsg(
        wallet=req_wallet.wallet,
        **signed_order.msg.dict()
    )

    return {'signed_msg': msg.to_hex_data()}


@router.post("/order/broadcast")
async def broadcast_order(
    signed_order: SignOrderSchema,
    background_tasks: BackgroundTasks,
    req_wallet: WalletConfig = Depends(get_wallet),
    current_user: UserSettings = Depends(get_current_user),
    sync: bool = True,
):
    """Sign and broadcast a new order message to the exchange

    """
    if not req_wallet.has_permission(WalletPermission.TRADE):
        raise HTTPException(status_code=403, detail=f"No permission {WalletPermission.TRADE}")

    # check user has permission for this wallet
    if not user_has_wallet_permission(current_user, signed_order.wallet_name, WalletPermission.TRADE):
        raise HTTPException(
            status_code=403,
            detail=f"User has no permission {WalletPermission.TRADE} on wallet {signed_order.wallet_name}"
        )

    # create the message
    msg = NewOrderMsg(
        wallet=req_wallet.wallet,
        **signed_order.msg.dict()
    )

    background_tasks.add_task(increment_wallet_sequence, req_wallet)
    return await req_wallet.broadcast_msg(msg.to_hex_data(), sync=sync)
