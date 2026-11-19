# tiny-chess-01 engine source (readable; packed into main.py by `makefun compress`).
# A 0x88 chess engine: alpha-beta with a transposition table, principal variation search,
# late move reductions, null-move pruning, killer moves, a history heuristic, quiescence
# with full evasions in check, and a deterministic node budget per move.
import json,os,random,urllib.request

M=20000
I=30000
V={"p":100,"n":325,"b":335,"r":500,"q":1000,"k":0}
G=(33,31,18,14,-33,-31,-18,-14)
D=(17,15,-17,-15)
H=(16,-16,1,-1)
K=D+H
C="abcdefgh"
X={c:i for i,c in enumerate("PNBRQKpnbrqk")}

# Piece-square tables, written as formulas so they cost code, not data.
PAWN=[(0,0,4,8,14,24,40,0)[r]+(10 if f in(3,4)and r in(3,4,5)else 0)for r in range(8)for f in range(8)]
KNIGHT=[6*(min(f,7-f)+min(r,7-r))-20 for r in range(8)for f in range(8)]
BISHOP=[4*(min(f,7-f)+min(r,7-r))-8 for r in range(8)for f in range(8)]
ROOK=[(15 if r==6 else 0)+(5 if r==0 and f in(3,4)else 0)for r in range(8)for f in range(8)]
QUEEN=[2*(min(f,7-f)+min(r,7-r))-6 for r in range(8)for f in range(8)]
KING=[[20,25,10,0,0,10,25,20][f]for f in range(8)]+[max(-50,-15*r)for r in range(1,8)for f in range(8)]
T={"p":PAWN,"n":KNIGHT,"b":BISHOP,"r":ROOK,"q":QUEEN,"k":KING}


def bt():
    """The tables as 0x88 arrays, white and black mirrored."""
    w={};b={}
    for n,tbl in T.items():
        a=[0]*128
        for r in range(8):
            for f in range(8):
                a[(7-r)*16+f]=tbl[r*8+f]
        w[n]=a
        a=[0]*128
        for r in range(8):
            for f in range(8):
                a[r*16+f]=tbl[r*8+f]
        b[n]=a
    return w,b


W,B=bt()

# Zobrist keys, from a fixed seed so the hash is the same in every run.
R=random.Random(9)
ZF=[[R.getrandbits(64)for _ in range(128)]for _ in range(12)]
ZR=R.getrandbits(64)
ZC={c:R.getrandbits(64)for c in"K Q KQ k Kk Qk KQk q Kq Qq KQq kq Kkq Qkq KQkq".split()}
ZE=[R.getrandbits(64)for _ in range(128)]


def nm(i):return C[i&7]+str((i>>4)+1)


def ps(f):
    # A FEN to a state list: board, side, ep, castling, king squares, non-pawn material, hash, score.
    b=["."]*128
    q=f.split()
    for r,row in enumerate(q[0].split("/")):
        x=0
        for c in row:
            if c.isdigit():x+=int(c)
            else:
                b[(7-r)*16+x]=c;x+=1
    w=q[1]=="w"
    ca=q[2]
    ep=(int(q[3][1])-1)*16+C.index(q[3][0])if q[3]!="-"else-1
    s=0;np=0;kw=-1;kb=-1;h=0
    for i in range(128):
        p=b[i]
        if p==".":continue
        t=p.lower()
        h^=ZF[X[p]][i]
        if p.isupper():
            s+=V[t]+W[t][i]
            if t=="k":kw=i
        else:
            s-=V[t]+B[t][i]
            if t=="k":kb=i
        if t!="p"and t!="k":np+=V[t]
    h^=ZC.get(ca,0)
    if ep>=0:h^=ZE[ep]
    if not w:h^=ZR
    return[b,w,ep,ca,kw,kb,np,h,s]


def at(b,t,w):
    """Whether the square t is attacked by the side w."""
    n,o,r,q,k,kf="NBRQKP"if w else"nbrqkp"
    d=-16 if w else 16
    for s in(t+d-1,t+d+1):
        if not s&0x88 and b[s]==kf:return 1
    for x in G:
        s=t+x
        if not s&0x88 and b[s]==n:return 1
    for x in K:
        s=t+x
        if not s&0x88:
            if b[s]==k:return 1
            while 1:
                p=b[s]
                if p!=".":
                    if p==q or(x in H and p==r)or(x in D and p==o):return 1
                    break
                s+=x
                if s&0x88:break
    return 0


def gen(S,cp=0):
    """Every pseudo-legal move; cp=1 keeps captures only."""
    b=S[0];w=S[1];ep=S[2];ca=S[3]
    o=[];a=o.append
    for i in range(128):
        if i&0x88:continue
        p=b[i]
        if p==".":continue
        u=p.isupper()
        if u!=w:continue
        t=p.lower()
        if t=="p":
            d=16 if u else-16
            st=0x10 if u else 0x60
            la=0x70 if u else 0
            z=i+d
            if not z&0x88 and b[z]==".":
                if z&0xF0==la:
                    for pr in"qrbn":a((i,z,pr))
                elif not cp:
                    a((i,z,""))
                    if i&0xF0==st and b[i+2*d]==".":a((i,i+2*d,""))
            for x in(d-1,d+1):
                z=i+x
                if z&0x88:continue
                v=b[z]
                if v!="."and v.isupper()!=u:
                    if z&0xF0==la:
                        for pr in"qrbn":a((i,z,pr))
                    else:a((i,z,""))
                elif v=="."and z==ep:a((i,z,""))
        elif t=="n"or t=="k":
            for x in(G if t=="n"else K):
                z=i+x
                if not z&0x88:
                    v=b[z]
                    if v==".":
                        if not cp:a((i,z,""))
                    elif v.isupper()!=u:a((i,z,""))
            if t=="k"and not cp:
                for cr,fr,dr in(("K",4,1),("Q",4,-1),("k",0x74,1),("q",0x74,-1)):
                    if cr in ca and all(b[fr+dr*i]=="."for i in range(1,3 if dr>0 else 4))and not at(b,fr,not u)and not at(b,fr+dr,not u):a((fr,fr+2*dr,""))
        else:
            for x in(D if t=="b"else H if t=="r"else K):
                z=i+x
                while not z&0x88:
                    v=b[z]
                    if v==".":
                        if not cp:a((i,z,""))
                    else:
                        if v.isupper()!=u:a((i,z,""))
                        break
                    z+=x
    return o


def mk(S,m):
    """Make a move: the new state list."""
    b,w,ep,ca,kw,kb,np,h,s=S
    fr,to,pr=m
    p=b[fr];t=p.lower();cp=b[to]
    tb=W if w else B
    g=1 if w else-1
    nb=b[:]
    ns=s-g*(V[t]+tb[t][fr])+g*(V[t]+tb[t][to])
    nh=h^ZF[X[p]][fr]^ZF[X[p]][to]
    nw,nbk=kw,kb
    if t=="k":
        if w:nw=to
        else:nbk=to
    if cp!=".":
        c=cp.lower()
        ns+=V[c]+B[c][to]if cp.islower()else-(V[c]+W[c][to])
        nh^=ZF[X[cp]][to]
        if c!="p":np-=V[c]
    elif t=="p"and to==ep:
        cs=to+(-16 if w else 16)
        ns+=V["p"]+B["p"][cs]if w else-(V["p"]+W["p"][cs])
        nh^=ZF[X["p"if w else"P"]][cs]
        nb[cs]="."
    nb[to]=p
    nb[fr]="."
    if t=="k"and abs(to-fr)==2:
        if to>fr:rf,rt=fr+3,fr+1
        else:rf,rt=fr-4,fr-1
        r=nb[rf]
        nb[rt]=r
        nb[rf]="."
        ns+=g*(tb["r"][rt]-tb["r"][rf])
        nh^=ZF[X[r]][rf]^ZF[X[r]][rt]
    if pr:
        ns+=g*(V[pr]-V["p"]+tb[pr][to]-tb["p"][to])
        np+=V[pr]
        p=pr.upper()if w else pr
        nh^=ZF[X["P"if w else"p"]][to]^ZF[X[p]][to]
        nb[to]=p
    nc=ca
    for q,c in((0,"Q"),(7,"K"),(0x70,"q"),(0x77,"k")):
        if fr==q or to==q:nc=nc.replace(c,"")
    if t=="k":nc=nc.replace("K"if w else"k","").replace("Q"if w else"q","")
    if nc!=ca:nh^=ZC.get(ca,0)^ZC.get(nc,0)
    if not nc:nc="-"
    nep=(to+fr)//2 if t=="p"and abs(to-fr)==32 else-1
    if ep>=0:nh^=ZE[ep]
    if nep>=0:nh^=ZE[nep]
    return[nb,not w,nep,nc,nw,nbk,np,nh^ZR,ns]


TT={}
nd=0
pa=[]
kl=[[None,None]for _ in range(96)]
hi={}
BD=0


class Cut(Exception):pass


def od(S,mv,y,tm):
    # Order the moves: the table's, then captures, killers, history, the rest.
    b=S[0]
    k1,k2=kl[y]
    def key(m):
        s=hi.get(m,0)
        v=b[m[1]]
        if v!=".":s+=100000+V[v.lower()]*16-V[b[m[0]].lower()]
        elif m[2]:s+=150000
        if m==k1:s+=20000
        elif m==k2:s+=18000
        if m==tm:s+=400000
        return-s
    mv.sort(key=key)
    return mv


def qs(S,al,be,y):
    # Quiescence: out of check the eval stands, in check every evasion is searched.
    global nd
    nd+=1
    if nd>BD:raise Cut()
    b,w,kw,kb=S[0],S[1],S[4],S[5]
    ch=at(b,kw if w else kb,not w)
    if not ch:
        sa=S[8]if w else-S[8]
        if sa>=be:return be
        if sa>al:al=sa
    n=0
    for m in od(S,gen(S,0 if ch else 1),y%96,None):
        st=mk(S,m)
        if at(st[0],st[4]if w else st[5],not w):continue
        n+=1
        r=-qs(st,-be,-al,y+1)
        if r>=be:return be
        if r>al:al=r
    return-M+y if ch and not n else al


def ab(S,d,al,be,y,cn):
    # Alpha-beta with a null move, LMR and a transposition table.
    global nd
    nd+=1
    if nd>BD:raise Cut()
    b,w,ep,ca,kw,kb,np,h,s=S
    if h in pa:return 0
    e=TT.get(h)
    tm=None
    if e is not None:
        d0,fl,s0,tm=e
        if d0>=d:
            if fl==0:return s0
            if fl==1 and s0<=al:return al
            if fl==2 and s0>=be:return be
    ch=at(b,kw if w else kb,not w)
    if ch:d+=1
    if d<=0:return qs(S,al,be,y)
    if cn and not ch and d>2 and np>600:
        h2=h^ZR
        if ep>=0:h2^=ZE[ep]
        if-ab([b,not w,-1,ca,kw,kb,np,h2,s],d-3,-be,-be+1,y+1,0)>=be:return be
    mv=[]
    for m in gen(S):
        st=mk(S,m)
        if at(st[0],st[4]if w else st[5],not w):continue
        mv.append(m)
    if not mv:return-M+y if ch else 0
    od(S,mv,y%96,tm)
    bs=-I
    bm=mv[0]
    a0=al
    pa.append(h)
    for i,m in enumerate(mv):
        st=mk(S,m)
        qt=b[m[1]]=="."and not m[2]
        if i==0:r=-ab(st,d-1,-be,-al,y+1,1)
        else:
            rd=0
            if qt and d>=3 and i>=3 and not ch:rd=1 if i<8 else 2
            r=-ab(st,d-1-rd,-al-1,-al,y+1,1)
            if r>al and(rd or r<be):r=-ab(st,d-1,-be,-al,y+1,1)
        if r>bs:
            bs=r
            bm=m
        if r>al:al=r
        if al>=be:
            if qt:
                kp=kl[y%96]
                if kp[0]!=m:
                    kp[1]=kp[0]
                    kp[0]=m
                hi[m]=hi.get(m,0)+d*d
            break
    pa.pop()
    fl=0 if a0<bs<be else(1 if bs<=a0 else 2)
    if len(TT)<4e5:TT[h]=(d,fl,bs,bm)
    return bs


def bm(f,mo,bd):
    # The best move for a position, under a node budget.
    global nd,pa,BD
    BD=bd
    S=ps(f)
    kl[:]=[[None,None]for _ in range(96)]
    nd=0
    pa=[]
    rt=[]
    w=S[1]
    for m in gen(S):
        st=mk(S,m)
        if at(st[0],st[4]if w else st[5],not w):continue
        rt.append(m)
    if not rt:return mo[0]if mo else None
    bs=rt[0]
    for d in range(1,20):
        al,sc=-I,[]
        try:
            for m in rt:
                r=-ab(mk(S,m),d-1,-I,-al,1,1)
                sc.append((r,m))
                if r>al:al=r
        except Cut:
            if sc:bs=max(sc,key=lambda x:x[0])[1]
            break
        sc.sort(key=lambda x:-x[0])
        bs=sc[0][1]
        rt=[m for _,m in sc]
        if al>M-200:break
    u=nm(bs[0])+nm(bs[1])+(bs[2]or"")
    return u if u in mo else(mo[0]if mo else None)


def rq(p,d):return json.load(urllib.request.urlopen(os.environ["MAKEFUN_ENV_URL"]+p,d))


def pl():
    # Play the whole gauntlet: one game at a time, until the env says it is over.
    while 1:
        g=rq("/game",b"{}")
        st=g.get("status")
        if st=="done":break
        while st=="your_move":
            y=int(g["fen"].split()[5])
            g=rq("/move",json.dumps({"game":g["game"],"move":bm(g["fen"],g["legal_moves"],max(40000,95000-1900*y))}).encode())
            st=g.get("status")


if __name__=="__main__":pl()
