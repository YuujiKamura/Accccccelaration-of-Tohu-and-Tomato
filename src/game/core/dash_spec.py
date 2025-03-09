"""
[SPEC-DASH-001] プレイヤーダッシュ機能の仕様

このファイルはプレイヤーのダッシュ機能に関する仕様を定義します。
"""

class DashSpec:
    """ダッシュ機能の仕様定義
    
    各仕様項目にはユニークなIDが付与されています。
    仕様の変更は、必ずテストの変更を伴う必要があります。
    """
    
    # [SPEC-DASH-101] 基本パラメータ
    NORMAL_SPEED = 5.0
    DASH_SPEED = 8.0  # 通常速度の1.6倍
    ACCELERATION = 0.5
    FRICTION = 0.1
    
    # [SPEC-DASH-102] ヒートゲージパラメータ
    MAX_HEAT = 100
    INITIAL_HEAT = 0
    HEAT_INCREASE_RATE = 1.0  # ダッシュ中の上昇率/フレーム
    HEAT_RECOVERY_RATE = 0.2  # 通常時の回復率/フレーム
    DASH_DISABLE_THRESHOLD = 50  # この値より上ではダッシュ不可
    
    # [SPEC-DASH-103] カーブ移動パラメータ
    MAX_TURN_RATE = 10  # 最大旋回角度/フレーム
    INPUT_WEIGHT = 0.8  # 入力方向の重み
    MOMENTUM_WEIGHT = 0.2  # 現在の移動方向の重み
    NORMAL_GRIP = 1.0
    DASH_GRIP = 0.8 