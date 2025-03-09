import pygame
import asyncio

# 初期化
pygame.init()

# 画面設定
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("アクセラレーションオブ豆腐")

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# 実行中フラグ
running = True

# メインゲームループ
async def main():
    global running
    
    # ゲームオブジェクト
    x, y = WIDTH // 2, HEIGHT // 2
    radius = 50
    
    while running:
        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # 描画
        screen.fill(BLACK)
        pygame.draw.circle(screen, RED, (x, y), radius)
        
        # 更新
        pygame.display.flip()
        
        # ブラウザ用非同期処理
        await asyncio.sleep(0)

# エントリーポイント
if __name__ == "__main__":
    asyncio.run(main())
    pygame.quit() 