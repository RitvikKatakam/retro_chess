import sys
import math, time
import pygame

# ----------------- Config -----------------
BOARD_SIZE = 640
PANEL_W = 200
WIN_W = BOARD_SIZE + PANEL_W
WIN_H = BOARD_SIZE
SQ = BOARD_SIZE // 8
LIGHT = (238, 238, 210)
DARK = (118, 150, 86)
HILITE = (156, 204, 101)
SELECT = (247, 236, 109)
CHECK = (255, 102, 102)
TEXT = (25, 25, 25)
BG = (245, 245, 245)
FPS = 60

WHITE, BLACK = 'w', 'b'
UNICODE = {
    'wK': '♔', 'wQ': '♕', 'wR': '♖', 'wB': '♗', 'wN': '♘', 'wP': '♙',
    'bK': '♚', 'bQ': '♛', 'bR': '♜', 'bB': '♝', 'bN': '♞', 'bP': '♟',
}

PIECE_VALUE = {'K': 0, 'Q': 900, 'R': 500, 'B': 330, 'N': 320, 'P': 100}

# -------------- Board & Rules --------------
def initial_board():
    return [
        ['bR','bN','bB','bQ','bK','bB','bN','bR'],
        ['bP','bP','bP','bP','bP','bP','bP','bP'],
        [None]*8,[None]*8,[None]*8,[None]*8,
        ['wP','wP','wP','wP','wP','wP','wP','wP'],
        ['wR','wN','wB','wQ','wK','wB','wN','wR'],
    ]

def in_bounds(r,c): return 0<=r<8 and 0<=c<8
def color_of(p): return None if p is None else p[0]
def is_opp(p,q): return p and q and p[0] != q[0]
def clone(board): return [row[:] for row in board]
def king_pos(board, side):
    for r in range(8):
        for c in range(8):
            if board[r][c] == side+'K': return (r,c)
    return None

def slide_moves(board,r,c,dirs,side):
    moves=[]
    for dr,dc in dirs:
        nr, nc = r+dr, c+dc
        while in_bounds(nr,nc):
            if board[nr][nc] is None:
                moves.append((nr,nc))
            else:
                if color_of(board[nr][nc]) != side:
                    moves.append((nr,nc))
                break
            nr += dr; nc += dc
    return moves

def pseudo_moves_for(board,r,c):
    piece = board[r][c]
    if not piece: return []
    side, kind = piece[0], piece[1]
    mv = []
    if kind == 'P':
        forward = -1 if side==WHITE else 1
        start_row = 6 if side==WHITE else 1
        nr, nc = r+forward, c
        if in_bounds(nr,nc) and board[nr][nc] is None:
            mv.append((nr,nc))
            nr2 = r+2*forward
            if r==start_row and board[nr2][nc] is None:
                mv.append((nr2,nc))
        for dc in (-1,1):
            nr, nc = r+forward, c+dc
            if in_bounds(nr,nc) and is_opp(board[r][c], board[nr][nc]):
                mv.append((nr,nc))
    elif kind=='N':
        for dr,dc in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
            nr, nc = r+dr, c+dc
            if in_bounds(nr,nc) and color_of(board[nr][nc]) != side:
                mv.append((nr,nc))
    elif kind=='B': mv += slide_moves(board,r,c,[(-1,-1),(-1,1),(1,-1),(1,1)], side)
    elif kind=='R': mv += slide_moves(board,r,c,[(-1,0),(1,0),(0,-1),(0,1)], side)
    elif kind=='Q': mv += slide_moves(board,r,c,
        [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)], side)
    elif kind=='K':
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr==0 and dc==0: continue
                nr, nc = r+dr, c+dc
                if in_bounds(nr,nc) and color_of(board[nr][nc]) != side:
                    mv.append((nr,nc))
    return mv

def apply_move(board,src,dst):
    r,c = src; r2,c2 = dst
    piece = board[r][c]
    nb = clone(board)
    nb[r2][c2] = piece
    nb[r][c] = None
    if piece and piece[1]=='P' and (r2==0 or r2==7):
        nb[r2][c2] = piece[0] + 'Q'
    return nb

def attacked_by(board,r,c,attacker_side):
    for dr,dc in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
        nr,nc = r+dr, c+dc
        if in_bounds(nr,nc) and board[nr][nc]==attacker_side+'N':
            return True
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if dr==0 and dc==0: continue
            nr,nc = r+dr, c+dc
            if in_bounds(nr,nc) and board[nr][nc]==attacker_side+'K':
                return True
    pawn_dir = 1 if attacker_side==WHITE else -1
    for dc in (-1,1):
        nr,nc = r - pawn_dir, c+dc
        if in_bounds(nr,nc) and board[nr][nc]==attacker_side+'P':
            return True
    def ray(dirs,targets):
        for dr,dc in dirs:
            nr,nc = r+dr, c+dc
            while in_bounds(nr,nc):
                p = board[nr][nc]
                if p:
                    if color_of(p)==attacker_side and p[1] in targets:
                        return True
                    break
                nr+=dr; nc+=dc
        return False
    if ray([(-1,-1),(-1,1),(1,-1),(1,1)], {'B','Q'}): return True
    if ray([(-1,0),(1,0),(0,-1),(0,1)], {'R','Q'}): return True
    return False

def in_check(board,side):
    kp = king_pos(board,side)
    if not kp: return True
    return attacked_by(board,kp[0],kp[1],WHITE if side==BLACK else BLACK)

def legal_moves_for(board,r,c):
    piece = board[r][c]
    if not piece: return []
    side = piece[0]
    legal=[]
    for dst in pseudo_moves_for(board,r,c):
        nb = apply_move(board,(r,c),dst)
        if not in_check(nb, side):
            legal.append(dst)
    return legal

def all_legal_moves(board,side):
    result=[]
    for r in range(8):
        for c in range(8):
            if board[r][c] and board[r][c][0]==side:
                lm = legal_moves_for(board,r,c)
                if lm: result.append(((r,c),lm))
    return result

def game_status(board,side_to_move):
    legal = all_legal_moves(board,side_to_move)
    if legal: return 'ok', None
    if in_check(board,side_to_move):
        return 'checkmate', (BLACK if side_to_move==WHITE else WHITE)
    return 'stalemate', None

# -------------- AI --------------
def evaluate(board):
    score=0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p:
                val = PIECE_VALUE[p[1]]
                score += val if p[0]==WHITE else -val
    return score

def minimax(board,side,depth,alpha=-math.inf,beta=math.inf):
    status,_ = game_status(board,side)
    if depth==0 or status!='ok':
        val = evaluate(board)
        if status=='checkmate':
            val = -99999 if side==WHITE else 99999
        return val, None
    best_move=None
    moves=[]
    for src,dsts in all_legal_moves(board,side):
        for d in dsts:
            moves.append((board[d[0]][d[1]] is not None, src, d))
    moves.sort(reverse=True)
    if side==WHITE:
        best=-math.inf
        for _,src,dst in moves:
            nb = apply_move(board,src,dst)
            val,_ = minimax(nb,BLACK,depth-1,alpha,beta)
            if val>best:
                best=val; best_move=(src,dst)
            alpha=max(alpha,best)
            if beta<=alpha: break
        return best,best_move
    else:
        best=math.inf
        for _,src,dst in moves:
            nb = apply_move(board,src,dst)
            val,_ = minimax(nb,WHITE,depth-1,alpha,beta)
            if val<best:
                best=val; best_move=(src,dst)
            beta=min(beta,best)
            if beta<=alpha: break
        return best,best_move

def cpu_move(board,side,depth=2):
    _,mv = minimax(board,side,depth)
    return mv

# -------------- Button Class --------------
class Button:
    def __init__(self, x, y, w, h, text, font, color, action=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.color = color
        self.action = action

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        txt_surface = self.font.render(self.text, True, (0,0,0))
        txt_rect = txt_surface.get_rect(center=self.rect.center)
        screen.blit(txt_surface, txt_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# -------------- Game Class --------------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("--Retro-Chess-Game->")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI Symbol", 48)
        self.small = pygame.font.SysFont("Segoe UI", 20)
        self.human = WHITE  # default
        self.reset_game()

    def reset_game(self):
        self.board = initial_board()
        self.turn = WHITE
        self.selected=None
        self.legal=[]
        self.message="White to move"
        self.cpu_depth=2
        self.hint_move=None
        self.hint_count=0
        self.undo_count=0
        self.player_time=300
        self.cpu_time=300
        self.last_tick=time.time()
        self.history=[]
        self.build_buttons()

    def build_buttons(self):
        x0 = BOARD_SIZE + 10
        self.btn_white = Button(x0, 20, 120, 30, "Play White", self.small,
                                (240,240,240) if self.human==WHITE else (200,200,200))
        self.btn_black = Button(x0, 60, 120, 30, "Play Black", self.small,
                                (240,240,240) if self.human==BLACK else (200,200,200))
        self.btn_hint = Button(x0, 150, 120, 30, f"Hint ({2-self.hint_count})",
                               self.small, (240,240,180))
        self.btn_undo = Button(x0, 190, 120, 30, f"Undo ({3-self.undo_count})",
                               self.small, (200,220,240))
        self.btn_restart = Button(x0, 230, 120, 30, "Restart",
                                  self.small, (240,200,200))

    def save_state(self):
        self.history.append((clone(self.board), self.turn, self.player_time, self.cpu_time))

    def draw_board(self):
        for r in range(8):
            for c in range(8):
                col = LIGHT if (r+c)%2==0 else DARK
                pygame.draw.rect(self.screen, col, (c*SQ, r*SQ, SQ, SQ))
        if self.selected:
            sr,sc=self.selected
            pygame.draw.rect(self.screen, SELECT, (sc*SQ,sr*SQ,SQ,SQ))
            for r,c in self.legal:
                pygame.draw.rect(self.screen, HILITE, (c*SQ,r*SQ,SQ,SQ))
        if in_check(self.board, self.turn):
            kp=king_pos(self.board,self.turn)
            if kp: pygame.draw.rect(self.screen,CHECK,(kp[1]*SQ,kp[0]*SQ,SQ,SQ))
        if self.hint_move:
            src,dst = self.hint_move
            pygame.draw.rect(self.screen,(135,206,250),(dst[1]*SQ,dst[0]*SQ,SQ,SQ),4)

        for r in range(8):
            for c in range(8):
                p=self.board[r][c]
                if p:
                    surf = self.font.render(UNICODE[p], True, TEXT)
                    rect = surf.get_rect(center=(c*SQ+SQ//2,r*SQ+SQ//2+4))
                    self.screen.blit(surf, rect)

    def draw_panel(self):
        x0 = BOARD_SIZE
        pygame.draw.rect(self.screen, BG, (x0,0,PANEL_W,WIN_H))
        self.btn_white.color = (240,240,240) if self.human==WHITE else (200,200,200)
        self.btn_black.color = (240,240,240) if self.human==BLACK else (200,200,200)
        self.btn_white.draw(self.screen)
        self.btn_black.draw(self.screen)

        self.screen.blit(self.small.render(f"White: {int(self.player_time)}s",True,TEXT),(x0+10,100))
        self.screen.blit(self.small.render(f"Black: {int(self.cpu_time)}s",True,TEXT),(x0+10,120))
        self.btn_hint.text = f"Hint ({2-self.hint_count})"
        self.btn_undo.text = f"Undo ({3-self.undo_count})"
        self.btn_hint.color = (240,240,180) if self.hint_count<2 else (200,200,200)
        self.btn_undo.color = (200,220,240) if self.undo_count<3 else (180,180,180)
        self.btn_hint.draw(self.screen)
        self.btn_undo.draw(self.screen)
        self.btn_restart.draw(self.screen)
        self.screen.blit(self.small.render(self.message,True,TEXT), (x0+10, 280))

    def handle_click(self,pos):
        if pos[0]>=BOARD_SIZE:
            if self.btn_white.is_clicked(pos):
                self.human = WHITE
                self.reset_game()
            if self.btn_black.is_clicked(pos):
                self.human = BLACK
                self.reset_game()
            if self.btn_restart.is_clicked(pos):
                self.reset_game()
            if self.btn_undo.is_clicked(pos) and self.undo_count<3 and self.history:
                state = self.history.pop()
                self.board,self.turn,self.player_time,self.cpu_time = state
                self.undo_count += 1
            if self.btn_hint.is_clicked(pos) and self.hint_count<2:
                self.hint_move = cpu_move(self.board,self.human,self.cpu_depth)
                self.hint_count += 1
            return
        c = pos[0]//SQ
        r = pos[1]//SQ
        if self.turn != self.human: return
        piece = self.board[r][c]
        if piece and color_of(piece)==self.turn:
            self.selected=(r,c)
            self.legal=legal_moves_for(self.board,r,c)
        elif self.selected and (r,c) in self.legal:
            self.save_state()
            self.board = apply_move(self.board,self.selected,(r,c))
            self.selected=None; self.legal=[]
            self.hint_move=None
            self.after_move()

    def after_move(self):
        now=time.time()
        dt = now - self.last_tick
        if self.turn==self.human: self.player_time -= dt
        else: self.cpu_time -= dt
        self.last_tick = now
        self.turn = BLACK if self.turn==WHITE else WHITE
        status,winner = game_status(self.board,self.turn)
        if status=='ok':
            self.message = "White to move" if self.turn==WHITE else "Black to move"
        elif status=='checkmate':
            self.message = f"Checkmate! {'White' if winner==WHITE else 'Black'} wins"
        elif status=='stalemate':
            self.message = "Stalemate!"

    def cpu_step(self):
        if self.turn!=self.human:
            self.save_state()
            mv = cpu_move(self.board,self.turn,self.cpu_depth)
            if mv:
                self.board = apply_move(self.board,mv[0],mv[1])
            self.hint_move=None
            self.after_move()

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type==pygame.QUIT: pygame.quit(); sys.exit()
                if e.type==pygame.MOUSEBUTTONDOWN:
                    self.handle_click(e.pos)

            self.cpu_step()
            self.screen.fill((0,0,0))
            self.draw_board()
            self.draw_panel()
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__=="__main__":
    Game().run()
