# -*- coding: utf-8 -*-
import math
import random
from dataclasses import dataclass

import pygame


# ------------------------------
# 基本設定
# ------------------------------
WIDTH, HEIGHT = 960, 540
FPS = 60
TITLE = "Jump & Smile Adventure"

# 物理パラメータ
GRAVITY = 0.8
JUMP_POWER = 16
PLAYER_SPEED = 5
SCROLL_SPEED_BASE = 4

# ステージ設定
TOTAL_STAGES = 4
STAGE_LENGTH_PX = 3600  # 1ステージのスクロール距離（ピクセル）

# カラー（やさしいパレット）
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
SOFT_BLACK = (50, 50, 60)
RED = (255, 90, 90)
GREEN = (120, 220, 160)
BLUE = (120, 180, 255)
YELLOW = (255, 230, 120)
PURPLE = (170, 140, 255)
PINK = (255, 170, 220)
ORANGE = (255, 180, 140)
MINT = (170, 255, 220)

STAGE_THEMES = [
    {"bg1": (240, 248, 255), "bg2": (220, 235, 255), "ground": (180, 220, 180), "accent": BLUE},
    {"bg1": (255, 245, 240), "bg2": (255, 235, 225), "ground": (220, 200, 160), "accent": ORANGE},
    {"bg1": (245, 245, 255), "bg2": (235, 235, 255), "ground": (190, 210, 240), "accent": PURPLE},
    {"bg1": (245, 255, 245), "bg2": (230, 255, 240), "ground": (160, 220, 200), "accent": MINT},
]

# ------------------------------
# オーディオ
# ------------------------------
AUDIO = None  # Game初期化時に設定


def _generate_tone_sound(freq_hz: float, duration_ms: int, volume: float = 0.4) -> pygame.mixer.Sound:
    sample_rate = 44100
    n_samples = int(sample_rate * (duration_ms / 1000.0))
    buf = bytearray()
    amp = int(32767 * max(0.0, min(1.0, volume)))
    two_pi_f = 2.0 * math.pi * freq_hz
    for i in range(n_samples):
        t = i / sample_rate
        # 簡易サイン波
        s = int(amp * math.sin(two_pi_f * t))
        # 16bit little-endian ステレオ同値
        lo = s & 0xff
        hi = (s >> 8) & 0xff
        buf.extend((lo, hi, lo, hi))
    return pygame.mixer.Sound(buffer=bytes(buf))


class AudioManager:
    def __init__(self):
        # SFX（全体的に小さめ）
        self.sfx_jump = _generate_tone_sound(520, 90, 0.20)
        self.sfx_stomp = _generate_tone_sound(220, 120, 0.22)
        self.sfx_hit = _generate_tone_sound(110, 180, 0.22)
        self.sfx_pause = _generate_tone_sound(600, 80, 0.16)
        # BGM: シンプルな低音モチーフをパーツ化
        motif = [196, 0, 247, 0, 220, 0, 165, 0]
        self.bgm_parts = []
        for freq in motif:
            vol = 0.60 if freq > 0 else 0.0
            snd = _generate_tone_sound(max(freq, 1), 600 if freq > 0 else 120, 0.3)
            snd.set_volume(vol)
            self.bgm_parts.append(snd)
        self._bgm_index = 0
        self._bgm_timer = 0.0
        self._bgm_playing = False
        self._segment_sec = 0.6  # 一定テンポ

    def play_jump(self):
        self.sfx_jump.play()

    def play_stomp(self):
        self.sfx_stomp.play()

    def play_hit(self):
        self.sfx_hit.play()

    def play_pause(self):
        self.sfx_pause.play()

    def start_bgm(self):
        self._bgm_index = 0
        self._bgm_timer = 0.0
        self._bgm_playing = True
        if self.bgm_parts:
            self.bgm_parts[0].play()

    def stop_bgm(self):
        self._bgm_playing = False
        pygame.mixer.stop()

    def update(self, dt: float):
        if not self._bgm_playing or not self.bgm_parts:
            return
        self._bgm_timer += dt
        if self._bgm_timer >= self._segment_sec:
            self._bgm_timer = 0.0
            self._bgm_index = (self._bgm_index + 1) % len(self.bgm_parts)
            try:
                self.bgm_parts[self._bgm_index].play()
            except Exception:
                # 念のため安全に巻き戻す
                self._bgm_index = 0
                self.bgm_parts[0].play()


# ------------------------------
# フォントヘルパ
# ------------------------------

def get_japanese_font(size: int, *, bold: bool = False) -> pygame.font.Font:
    # よくある日本語フォント名を優先的に探す
    candidates = [
        "Noto Sans CJK JP",
        "Noto Sans JP",
        "NotoSerif CJK JP",
        "Yu Gothic",
        "Yu Gothic UI",
        "Meiryo",
        "MS Gothic",
        "MS PGothic",
        "TakaoGothic",
        "IPAGothic",
        "VL Gothic",
    ]
    for name in candidates:
        path = pygame.font.match_font(name, bold=bold)
        if path:
            try:
                return pygame.font.Font(path, size)
            except Exception:
                pass
    # 見つからなければデフォルト
    return pygame.font.SysFont(None, size, bold=bold)


# ------------------------------
# データクラス
# ------------------------------
@dataclass
class Platform:
    rect: pygame.Rect
    color: tuple
    moving: bool = False
    move_range: int = 0
    move_speed: float = 0.0
    move_phase: float = 0.0
    vertical: bool = False
    # 追加: 動く足場の慣性用
    prev_x: int = 0
    prev_y: int = 0
    dx_local: int = 0

    def update(self):
        if not self.moving:
            return
        # シンプルな往復運動（フレーム基準）
        prev = math.sin(self.move_phase) * self.move_range
        self.move_phase += self.move_speed
        curr = math.sin(self.move_phase) * self.move_range
        delta = int(curr - prev)
        if self.vertical:
            self.rect.y += delta
        else:
            self.rect.x += delta


@dataclass
class Projectile:
    rect: pygame.Rect
    vx: float
    vy: float
    color: tuple

    def update(self):
        # フレームごとに移動
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)


class Boss:
    def __init__(self, x: int, y: int, stage_index: int):
        self.rect = pygame.Rect(x, y, 120, 100)
        self.color = STAGE_THEMES[stage_index]["accent"]
        self.max_hp = 3 + stage_index  # ステージが進むと少し硬く
        self.hp = self.max_hp
        self.jump_cooldown = 0.0
        self.shoot_cooldown = 1.0
        self.on_ground = False
        self.vx = -2  # 少し左へ歩く
        self.vy = 0.0
        self.alive = True
        # 追加: 行動バリエーション
        self.action_timer = 0.0
        self.dash_timer = 0.0
        self.last_x = x
        self.stuck_timer = 0.0

    def update(self, dt: float, platforms: list, projectiles: list):
        if not self.alive:
            return

        self.action_timer += dt

        # 重力
        self.vy += GRAVITY
        self.rect.y += int(self.vy)

        # 地面/足場との衝突
        self.on_ground = False
        on_platform = None
        for p in platforms:
            if self.rect.colliderect(p.rect):
                # 上から着地
                if self.vy > 0 and self.rect.bottom - p.rect.top < 30:
                    self.rect.bottom = p.rect.top
                    self.vy = 0
                    self.on_ground = True
                    on_platform = p

        # 足場端で方向転換（落下しにくく）
        if self.on_ground and on_platform:
            edge_margin = 12
            if self.rect.centerx <= on_platform.rect.left + edge_margin:
                self.vx = abs(self.vx)
            elif self.rect.centerx >= on_platform.rect.right - edge_margin:
                self.vx = -abs(self.vx)

        # 横移動（壁があれば跳ね返る簡易AI）
        self.rect.x += int(self.vx)
        hit_wall = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vx > 0:
                    self.rect.right = p.rect.left
                else:
                    self.rect.left = p.rect.right
                self.vx *= -1
                hit_wall = True

        # スタック検知（位置がほぼ変わらない）で緊急アクション
        if abs(self.rect.x - self.last_x) < 2:
            self.stuck_timer += dt
        else:
            self.stuck_timer = 0.0
        self.last_x = self.rect.x

        if self.stuck_timer > 1.0:
            # 小ジャンプ＋反転で脱出
            self.vy = -14
            self.vx *= -1
            self.stuck_timer = 0.0

        # ランダム行動: ダッシュや大ジャンプ
        if self.on_ground and self.action_timer > 1.2:
            self.action_timer = 0.0
            if random.random() < 0.4:
                # ダッシュ
                self.vx = -6 if self.vx < 0 else 6
                self.dash_timer = 0.6
            else:
                # 大ジャンプ
                self.vy = -16

        if self.dash_timer > 0:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                # 通常速度へ
                self.vx = -2 if self.vx < 0 else 2

        # たまにジャンプ（従来挙動も維持）
        self.jump_cooldown -= dt
        if self.on_ground and self.jump_cooldown <= 0 and random.random() < 0.5:
            self.vy = -12
            self.jump_cooldown = random.uniform(1.0, 2.0)

        # 弾を発射
        self.shoot_cooldown -= dt
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = random.uniform(1.2, 2.4)
            vy = random.uniform(-3.0, -1.0)
            projectiles.append(Projectile(self.rect.copy().inflate(-90, -60).move(-10, 40), -6 if self.vx <= 0 else 6, vy, self.color))

        # 画面外クランプ（左右・上、下は軽く抑える）
        if self.rect.left < 0:
            self.rect.left = 0
            self.vx = abs(self.vx)
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.vx = -abs(self.vx)
        if self.rect.top < 0:
            self.rect.top = 0
            if self.vy < 0:
                self.vy = 0
        if self.rect.bottom > HEIGHT - 10:
            self.rect.bottom = HEIGHT - 10
            if self.vy > 0:
                self.vy = 0

    def damage(self):
        if not self.alive:
            return
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False


class Player:
    def __init__(self, x: int, y: int):
        self.rect = pygame.Rect(x, y, 48, 48)
        self.color_body = PINK
        self.color_face = WHITE
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.health = 3
        self.invincible_timer = 0.0  # 開始時は無敵なし
        # 二段ジャンプとコヨーテタイム
        self.max_jumps = 2
        self.jumps_remaining = self.max_jumps
        self.coyote_timer = 0.0
        # 安全な復活位置
        self.last_safe_x = x
        self.last_safe_y = y
        # 接地している足場
        self.grounded_on = None
        # 復活浮遊タイマー（浮かんでから落下）
        self.respawn_float_timer = 0.0

    def control(self, keys: pygame.key.ScancodeWrapper):
        self.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = PLAYER_SPEED

    def try_jump(self):
        # 地上にいるか、直前に地上だった（コヨーテ）場合は一段目として扱う
        if self.coyote_timer > 0:
            self.vy = -JUMP_POWER
            self.on_ground = False
            self.coyote_timer = 0.0
            self.jumps_remaining = self.max_jumps - 1
            if AUDIO:
                AUDIO.play_jump()
            return True
        # 空中なら残ジャンプ回数で二段目を許可
        if self.jumps_remaining > 0:
            self.vy = -JUMP_POWER
            self.jumps_remaining -= 1
            if AUDIO:
                AUDIO.play_jump()
            return True
        return False

    def update(self, dt: float, platforms: list):
        # 復活直後の浮遊フェーズ
        if self.respawn_float_timer > 0.0:
            self.respawn_float_timer -= dt
            # 浮遊中は位置と速度を固定（微小な点滅だけ継続）
            self.vx = 0
            self.vy = 0
            if self.invincible_timer > 0:
                self.invincible_timer -= dt
            return

        # 重力
        self.vy += GRAVITY

        # 横移動
        self.rect.x += int(self.vx)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vx > 0:
                    self.rect.right = p.rect.left
                elif self.vx < 0:
                    self.rect.left = p.rect.right

        # 縦移動
        self.rect.y += int(self.vy)
        was_on_ground = self.on_ground
        self.on_ground = False
        contact_platform = None
        for p in platforms:
            if self.rect.colliderect(p.rect):
                # 上から着地
                if self.vy > 0 and self.rect.bottom - p.rect.top < 30:
                    self.rect.bottom = p.rect.top
                    self.vy = 0
                    self.on_ground = True
                    contact_platform = p
                    # 着地直後に足場の移動量を反映（滑り防止）
                    self.rect.x += p.dx_local
                # 下から頭をぶつけた
                elif self.vy < 0 and p.rect.bottom - self.rect.top < 30:
                    self.rect.top = p.rect.bottom
                    self.vy = 0

        # 接地中は毎フレーム、足場の移動量を反映
        if self.on_ground and contact_platform is not None:
            self.rect.x += contact_platform.dx_local
            self.grounded_on = contact_platform
        else:
            self.grounded_on = None

        # コヨーテタイムとジャンプリセット
        if self.on_ground:
            self.coyote_timer = 0.12
            self.jumps_remaining = self.max_jumps
            # セーフポイント更新（画面内の端に寄せすぎない）
            self.last_safe_x = max(40, min(self.rect.x, WIDTH - 80))
            self.last_safe_y = self.rect.y
        else:
            self.coyote_timer = max(0.0, self.coyote_timer - dt)

        # 画面端クランプ（左右・上）
        if self.rect.left < 0:
            self.rect.left = 0
            if self.vx < 0:
                self.vx = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
            if self.vx > 0:
                self.vx = 0
        if self.rect.top < 0:
            self.rect.top = 0
            if self.vy < 0:
                self.vy = 0

        # 画面外に落下したら軽いペナルティ（従来通り）
        if self.rect.top > HEIGHT + 200:
            self.take_damage()
            self.respawn()

        # 無敵時間カウントダウン
        if self.invincible_timer > 0:
            self.invincible_timer -= dt

    def take_damage(self):
        if self.invincible_timer > 0:
            return
        self.health -= 1
        self.invincible_timer = 1.2
        if AUDIO:
            AUDIO.play_hit()

    def respawn(self):
        # 直近の着地地点に復活（さらに高めに）
        self.rect.x = int(self.last_safe_x)
        self.rect.y = int(self.last_safe_y - 56)
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        # 浮遊フェーズ開始（スマブラ風）
        self.respawn_float_timer = 0.9
        # 無敵延長
        self.invincible_timer = 1.8
        # 二段ジャンプリセット
        self.jumps_remaining = self.max_jumps
        self.coyote_timer = 0.0

    def draw(self, surface: pygame.Surface):
        # 無敵中は点滅（約10Hz）
        if self.invincible_timer > 0 and int(pygame.time.get_ticks() * 0.01) % 2 == 0:
            return
        # 体（丸っこい四角）
        pygame.draw.rect(surface, self.color_body, self.rect, border_radius=12)
        # 顔
        eye_w, eye_h = 8, 10
        left_eye = pygame.Rect(self.rect.x + 12, self.rect.y + 12, eye_w, eye_h)
        right_eye = pygame.Rect(self.rect.x + 28, self.rect.y + 12, eye_w, eye_h)
        mouth = pygame.Rect(self.rect.x + 18, self.rect.y + 28, 12, 6)
        pygame.draw.ellipse(surface, self.color_face, left_eye)
        pygame.draw.ellipse(surface, self.color_face, right_eye)
        pygame.draw.rect(surface, self.color_face, mouth, border_radius=3)


# ------------------------------
# ステージ管理
# ------------------------------
class StageManager:
    def __init__(self):
        self.stage_index = 0
        self.distance_left = STAGE_LENGTH_PX
        self.scroll_speed = SCROLL_SPEED_BASE
        self.platforms: list = []
        self.projectiles: list = []
        self.boss = None
        self.arena_mode = False
        self.ground_y = HEIGHT - 80
        self.right_spawn_x = WIDTH + 200
        self.spawn_timer = 0.0
        self._init_stage_platforms()

    def current_theme(self):
        # 範囲外参照を防止
        safe_index = max(0, min(self.stage_index, TOTAL_STAGES - 1))
        return STAGE_THEMES[safe_index]

    def _init_stage_platforms(self):
        self.platforms.clear()
        # 地面を複数並べてスクロール
        for i in range(8):
            rect = pygame.Rect(i * 300, self.ground_y, 320, 80)
            self.platforms.append(Platform(rect, self.current_theme()["ground"]))

        # 少し足場
        for i in range(4):
            px = 350 + i * 450
            py = self.ground_y - random.choice([120, 160, 200])
            w = random.choice([120, 160])
            moving = random.random() < 0.3
            self.platforms.append(
                Platform(
                    pygame.Rect(px, py, w, 20),
                    self.current_theme()["accent"],
                    moving=moving,
                    move_range=40 if moving else 0,
                    move_speed=0.08 if moving else 0.0,
                    vertical=False,
                )
            )

    def next_stage(self):
        self.stage_index += 1
        if self.stage_index >= TOTAL_STAGES:
            return False
        self.distance_left = STAGE_LENGTH_PX
        self.scroll_speed = SCROLL_SPEED_BASE + self.stage_index  # 少しずつ速く
        self.projectiles.clear()
        self.boss = None
        self.arena_mode = False
        self._init_stage_platforms()
        return True

    def enter_boss_arena(self):
        self.arena_mode = True
        self.projectiles.clear()
        # ボス用: 地面のみ（浮遊足場は無し）
        self.platforms = [
            Platform(pygame.Rect(0, self.ground_y, WIDTH, 80), self.current_theme()["ground"]),
        ]
        self.boss = Boss(WIDTH - 140, self.ground_y - 100, self.stage_index)

    def spawn_platforms(self, dt: float):
        if self.arena_mode:
            return
        self.spawn_timer -= dt
        if self.spawn_timer <= 0 and self.distance_left > 600:
            self.spawn_timer = random.uniform(0.6, 1.0)
            gap = random.randint(60, 180)
            w = random.choice([120, 160, 200])
            py = self.ground_y - random.choice([100, 140, 180, 220])
            moving = random.random() < (0.2 + 0.05 * self.stage_index)
            platform = Platform(
                pygame.Rect(self.right_spawn_x + gap, py, w, 20),
                self.current_theme()["accent"],
                moving=moving,
                move_range=40 if moving else 0,
                move_speed=0.06 if moving else 0.0,
                vertical=random.random() < 0.2 if moving else False,
            )
            self.platforms.append(platform)

    def update(self, dt: float):
        # スクロールと距離
        if not self.arena_mode:
            self.distance_left = max(0, self.distance_left - self.scroll_speed)

        # 足場の移動/更新
        for p in self.platforms:
            # 前フレーム位置保存
            prev_x, prev_y = p.rect.x, p.rect.y
            p.update()
            # ローカル移動量（自前の動きのみ）
            p.dx_local = p.rect.x - prev_x
            # スクロール分を適用
            if not self.arena_mode:
                p.rect.x -= self.scroll_speed
            # 旧prev更新
            p.prev_x, p.prev_y = p.rect.x, p.rect.y

        # 画面外の足場を整理
        self.platforms = [p for p in self.platforms if p.rect.right > -300]

        # 自動生成
        self.spawn_platforms(dt)

        # ボス処理
        if not self.arena_mode and self.distance_left <= 0 and self.boss is None:
            self.enter_boss_arena()
        if self.boss:
            self.boss.update(dt, self.platforms, self.projectiles)

        # 弾の更新
        for proj in self.projectiles:
            proj.update()
        self.projectiles = [b for b in self.projectiles if -100 < b.rect.right and b.rect.left < WIDTH + 100 and -100 < b.rect.bottom and b.rect.top < HEIGHT + 100]

    def draw_background(self, surface: pygame.Surface):
        theme = self.current_theme()
        # グラデ背景っぽく
        surface.fill(theme["bg1"])
        for i in range(4):
            parallax = 0.2 + 0.15 * i
            y = 120 + i * 80
            w = 140
            for x in range(-w, WIDTH + w, w + 40):
                rect = pygame.Rect(x - int((pygame.time.get_ticks() * parallax * 0.05) % (w + 40)), y, w, 24)
                pygame.draw.rect(surface, theme["bg2"], rect, border_radius=12)

    def draw_platforms(self, surface: pygame.Surface):
        for p in self.platforms:
            pygame.draw.rect(surface, p.color, p.rect, border_radius=6)

    def check_player_collisions(self, player):
        # ボス弾
        for proj in self.projectiles:
            if player.rect.colliderect(proj.rect):
                player.take_damage()
                # 当たった弾は消す
                proj.rect.x = -9999

        # ボスとの当たり
        if self.boss and self.boss.alive:
            if player.rect.colliderect(self.boss.rect):
                # 接触方向を判定
                overlap_top = player.rect.bottom - self.boss.rect.top
                overlap_bottom = self.boss.rect.bottom - player.rect.top
                overlap_left = player.rect.right - self.boss.rect.left
                overlap_right = self.boss.rect.right - player.rect.left
                min_overlap = min(overlap_top, overlap_bottom, overlap_left, overlap_right)

                is_falling = player.vy > 0
                stomp_margin = 18
                stompable = is_falling and player.rect.bottom <= self.boss.rect.top + stomp_margin

                if stompable and min_overlap == overlap_top:
                    # マリオ風踏みつけ：強めの縦反発、ジャンプ回数リセット
                    player.rect.bottom = self.boss.rect.top
                    player.vy = -JUMP_POWER * 1.05
                    player.jumps_remaining = player.max_jumps - 1
                    self.boss.vy = max(self.boss.vy, 6)
                    self.boss.damage()
                    if AUDIO:
                        AUDIO.play_stomp()
                else:
                    # 斜めや側面の場合は押し戻しのみ（被弾しない）
                    if min_overlap == overlap_left:
                        player.rect.right = self.boss.rect.left
                    elif min_overlap == overlap_right:
                        player.rect.left = self.boss.rect.right
                    elif min_overlap == overlap_bottom:
                        player.rect.top = self.boss.rect.bottom
                        player.vy = max(player.vy, 0)
                    else:
                        # 上からだが条件外（落下でない等）→軽く押し上げ
                        player.rect.bottom = self.boss.rect.top
                        player.vy = min(player.vy, 0)


# ------------------------------
# UI/テキスト
# ------------------------------
class UI:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        # 日本語フォント（見つからなければデフォルト）。サイズを少し小さめに
        self.font = get_japanese_font(28)
        self.font_big = get_japanese_font(56)

    def draw_top(self, player: "Player", stage_index: int, distance_left: int):
        # ハート
        for i in range(3):
            cx = 20 + i * 28
            cy = 20
            color = RED if i < player.health else (200, 200, 200)
            pygame.draw.circle(self.surface, color, (cx, cy), 8)
            pygame.draw.circle(self.surface, color, (cx + 10, cy), 8)
            pygame.draw.polygon(self.surface, color, [(cx - 6, cy + 2), (cx + 16, cy + 2), (cx + 5, cy + 16)])

        # ステージと残距離
        text = self.font.render(f"Stage {stage_index + 1}/{TOTAL_STAGES}", True, SOFT_BLACK)
        self.surface.blit(text, (20, 44))
        if distance_left > 0:
            meter = max(0, min(1.0, distance_left / STAGE_LENGTH_PX))
            pygame.draw.rect(self.surface, (220, 220, 220), (180, 52, 200, 10), border_radius=5)
            pygame.draw.rect(self.surface, (120, 200, 120), (180, 52, int(200 * meter), 10), border_radius=5)

    def draw_center_message(self, message: str, color=SOFT_BLACK):
        label = self.font_big.render(message, True, color)
        rect = label.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.surface.blit(label, rect)

    def draw_footer(self, message: str, color=(90, 90, 110)):
        label = self.font.render(message, True, color)
        rect = label.get_rect(center=(WIDTH // 2, HEIGHT - 24))
        self.surface.blit(label, rect)


# ------------------------------
# メインゲーム
# ------------------------------
class Game:
    def __init__(self):
        pygame.init()
        # ミキサー
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
        except Exception:
            pass
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.ui = UI(self.screen)

        global AUDIO
        AUDIO = AudioManager()

        self.player = Player(160, HEIGHT - 200)
        self.stage = StageManager()

        self.running = True
        self.scene = "title"  # title, play, gameover, win
        self.pause = False
        # 入力の立ち上がり検出（キーボード/ゲームパッド別）
        self.kb_jump_prev = False
        self.pad_jump_prev = False
        # 決定ボタン（スタート/リスタート用）の前回状態
        self.pad_confirm_prev = False
        # 終了用 長押しタイマー（複数パターン）
        self.pad_quit_hold_options = 0.0
        self.pad_quit_hold_lr = 0.0
        self.pad_quit_hold_combo = 0.0
        # コントローラーのポーズボタンの前回状態
        self.pause_was_down = False
        # ジョイスティック初期化と取得（PS4コントローラー対応）
        self.joy = None
        self.joys = []
        self.joy_idx = None
        self._select_joystick()

        # タイトルBGM開始
        AUDIO.start_bgm()

    def reset(self):
        self.player = Player(160, HEIGHT - 200)
        self.stage = StageManager()
        self.scene = "title"
        self.pause = False
        self.kb_jump_prev = False
        self.pad_jump_prev = False
        self.pause_was_down = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_r:
                    self.reset()
                # タイトル開始
                if self.scene == "title":
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.scene = "play"
                # ゲームオーバー/勝利からの再スタート（キーボード）
                if self.scene in ("gameover", "win"):
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.reset()
                        self.scene = "play"
                # プレイ中のポーズ
                if self.scene == "play":
                    if event.key == pygame.K_p:
                        self.pause = not self.pause
                        if AUDIO:
                            AUDIO.play_pause()
            elif event.type == pygame.JOYDEVICEADDED:
                self._select_joystick()
            elif event.type == pygame.JOYDEVICEREMOVED:
                self._select_joystick()

    def update(self, dt: float):
        # ゲームパッド汎用入力（どのシーンでも）
        self._apply_global_gamepad_inputs(dt)

        if self.scene != "play" or self.pause:
            # ポーズ状態でもポーズ解除のため、コントローラーだけチェック
            self._update_gamepad_pause_toggle()
            return

        keys = pygame.key.get_pressed()
        self.player.control(keys)
        # キーボードのジャンプ（立ち上がりのみ）
        kb_jump_now = bool(keys[pygame.K_SPACE])
        if kb_jump_now and not self.kb_jump_prev:
            self.player.try_jump()
        self.kb_jump_prev = kb_jump_now

        # ゲームパッド入力の合成
        self._apply_gamepad_input()

        self.player.update(dt, self.stage.platforms)
        self.stage.update(dt)
        self.stage.check_player_collisions(self.player)

        # ステージクリア/ボス撃破
        if self.stage.boss and not self.stage.boss.alive:
            advanced = self.stage.next_stage()
            if not advanced:
                self.scene = "win"
            # BGM継続（必要ならここで切替実装可能）

        # プレイヤー体力
        if self.player.health <= 0:
            self.scene = "gameover"

        # BGM更新
        if AUDIO:
            AUDIO.update(dt)

    def draw(self):
        self.stage.draw_background(self.screen)
        self.stage.draw_platforms(self.screen)

        # ボス
        if self.stage.boss and self.stage.boss.alive:
            pygame.draw.rect(self.screen, self.stage.boss.color, self.stage.boss.rect, border_radius=12)
            # 顔パーツ
            b = self.stage.boss.rect
            eye_w, eye_h = 14, 18
            left_eye = pygame.Rect(b.x + 28, b.y + 22, eye_w, eye_h)
            right_eye = pygame.Rect(b.x + b.w - 28 - eye_w, b.y + 22, eye_w, eye_h)
            mouth = pygame.Rect(b.centerx - 16, b.y + 56, 32, 12)
            pygame.draw.ellipse(self.screen, WHITE, left_eye)
            pygame.draw.ellipse(self.screen, WHITE, right_eye)
            pygame.draw.rect(self.screen, WHITE, mouth, border_radius=6)
            # ボスHPバー
            bar_w = 240
            hp_rate = self.stage.boss.hp / self.stage.boss.max_hp
            pygame.draw.rect(self.screen, (220, 220, 220), (WIDTH - bar_w - 20, 20, bar_w, 12), border_radius=6)
            pygame.draw.rect(self.screen, (250, 120, 160), (WIDTH - bar_w - 20, 20, int(bar_w * hp_rate), 12), border_radius=6)

        # 弾
        for b in self.stage.projectiles:
            pygame.draw.ellipse(self.screen, self.stage.current_theme()["accent"], b.rect)

        # プレイヤー
        self.player.draw(self.screen)

        # UI
        self.ui.draw_top(self.player, self.stage.stage_index, self.stage.distance_left)

        # シーン別メッセージ
        if self.scene == "title":
            self.ui.draw_center_message("Jump & Smile Adventure")
            self.ui.draw_footer("スペース/Enterでスタート  |  ←→で移動、スペースでジャンプ、Pでポーズ、Rでリスタート")
        elif self.scene == "gameover":
            self.ui.draw_center_message("GAME OVER", color=(180, 60, 60))
            self.ui.draw_footer("スペース/Enter/R でリスタート  /  Esc で終了")
        elif self.scene == "win":
            self.ui.draw_center_message("YOU WIN! おめでとう！", color=(60, 160, 120))
            self.ui.draw_footer("スペース/Enter/R で最初から  /  Esc で終了")
        elif self.pause:
            self.ui.draw_center_message("PAUSED")
            self.ui.draw_footer("P で再開 / Esc で終了")

        pygame.display.flip()

    def run(self):
        while self.running:
            dt_ms = self.clock.tick(FPS)
            dt = dt_ms / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

    def _apply_gamepad_input(self):
        if not self.joy:
            self._update_gamepad_pause_toggle()
            return
        # デッドゾーン
        deadzone = 0.25

        # 左右: 左スティックX or D-PadX
        axis_x = 0.0
        try:
            axis_x = float(self.joy.get_axis(0))
        except Exception:
            axis_x = 0.0
        hat_x = 0
        try:
            # 多くのパッドで HAT は (x, y)
            hx, hy = self.joy.get_hat(0)
            hat_x = hx
        except Exception:
            hat_x = 0

        pad_vx = 0
        if abs(axis_x) >= deadzone:
            pad_vx = int(axis_x * PLAYER_SPEED)
        elif hat_x != 0:
            pad_vx = hat_x * PLAYER_SPEED

        # 既存のキーボード移動が無いときだけゲームパッド速度を適用
        if self.player.vx == 0 and pad_vx != 0:
            self.player.vx = max(-PLAYER_SPEED, min(PLAYER_SPEED, pad_vx))

        # ジャンプ: ×/A/南ボタン（環境差を吸収）
        def _btn(i: int) -> bool:
            try:
                return bool(self.joy.get_button(i))
            except Exception:
                return False
        jump_pressed = _btn(0) or _btn(1) or _btn(2)
        if jump_pressed and not self.pad_jump_prev:
            self.player.try_jump()
        self.pad_jump_prev = bool(jump_pressed)

        # ポーズは別関数へ
        self._update_gamepad_pause_toggle()

    def _update_gamepad_pause_toggle(self):
        if not self.joy:
            return
        def _btn(i: int) -> bool:
            try:
                return bool(self.joy.get_button(i))
            except Exception:
                return False
        # OPTIONS/START/中央ボタン候補
        paused_btn = _btn(7) or _btn(8) or _btn(9) or _btn(10)
        if paused_btn and not self.pause_was_down:
            self.pause = not self.pause
            if AUDIO:
                AUDIO.play_pause()
        self.pause_was_down = paused_btn

    def _select_joystick(self):
        pygame.joystick.init()
        self.joys = []
        for i in range(pygame.joystick.get_count()):
            try:
                j = pygame.joystick.Joystick(i)
                j.init()
                self.joys.append(j)
            except Exception:
                pass
        # 優先: DualShock/PS/SONY を名前に含むもの
        preferred = None
        for idx, j in enumerate(self.joys):
            name = (j.get_name() or "").lower()
            if any(k in name for k in ["dualshock", "dual sense", "dualsense", "ps4", "ps5", "sony", "wireless controller"]):
                preferred = idx
                break
        if preferred is None and self.joys:
            preferred = 0
        self.joy_idx = preferred
        self.joy = self.joys[preferred] if preferred is not None else None

    def _apply_global_gamepad_inputs(self, dt: float):
        if not self.joy:
            return
        def _btn(i: int) -> bool:
            try:
                return bool(self.joy.get_button(i))
            except Exception:
                return False

        # 候補ボタン
        btn_options = _btn(7) or _btn(9)  # 環境差を吸収
        btn_share = _btn(8) or _btn(6)
        btn_l1 = _btn(4)
        btn_r1 = _btn(5)

        # 1) Options長押し
        if btn_options:
            self.pad_quit_hold_options += dt
            if self.pad_quit_hold_options >= 1.2:
                self.running = False
                return
        else:
            self.pad_quit_hold_options = 0.0

        # 2) L1+R1同時長押し
        if btn_l1 and btn_r1:
            self.pad_quit_hold_lr += dt
            if self.pad_quit_hold_lr >= 1.2:
                self.running = False
                return
        else:
            self.pad_quit_hold_lr = 0.0

        # 3) Options+Share同時長押し
        if btn_options and btn_share:
            self.pad_quit_hold_combo += dt
            if self.pad_quit_hold_combo >= 1.2:
                self.running = False
                return
        else:
            self.pad_quit_hold_combo = 0.0

        # 決定（短押し）
        confirm = _btn(0) or _btn(1) or _btn(2) or btn_options
        if confirm and not self.pad_confirm_prev:
            if self.scene == "title":
                self.scene = "play"
                if AUDIO:
                    AUDIO.play_pause()
            elif self.scene in ("gameover", "win"):
                self.reset()
                self.scene = "play"
                if AUDIO:
                    AUDIO.play_pause()
        self.pad_confirm_prev = confirm


if __name__ == "__main__":
    try:
        Game().run()
    except Exception as e:
        # ここも日本語を出せるようにしておく
        print("エラーが発生しました:", e)
    finally:
        pygame.quit()
