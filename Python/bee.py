#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пчельний блокчейн: peer-to-peer, gossip, PoS-голосование, статистика, graceful shutdown.
Только стандартная библиотека Python 3.8+.
"""
import argparse, dataclasses, enum, hashlib, itertools, json, pathlib, queue, random, signal, socket, threading, time
from typing import Optional, List, Dict, Set

BLOCK_SEC  = 30
GOSSIP_SEC = 5
WINDOW_MIN = 5

# ---------- блоки ----------
@dataclasses.dataclass
class Block:
    index: int
    timestamp: float
    bee_id: int
    nectar_kg: float
    prev_hash: str
    hash: str

    @classmethod
    def genesis(cls):
        return cls(0, time.monotonic(), 0, 0.0, "0",
                   hashlib.sha256(b"genesis").hexdigest())

    def next(self, bee_id, nectar):
        payload = f"{self.index+1}{bee_id}{nectar}{self.hash}".encode()
        return Block(self.index+1, time.monotonic(), bee_id, nectar,
                     self.hash, hashlib.sha256(payload).hexdigest())

# ---------- роли ----------
class BeeRole(enum.Enum):
    HONEST = "honest"
    THIEF  = "thief"

# ---------- локальная цепь ----------
class LocalChain:
    def __init__(self, node_id: int, cheat_prob: float = 0.0):
        self.node_id   = node_id
        self.cheat_prob = cheat_prob
        self.chain: List[Block] = [Block.genesis()]
        self.lock      = threading.Lock()
        self.votes: Dict[str, Set[int]] = {}

    @property
    def head(self) -> Block:
        return self.chain[-1]

    def add(self, blk: Block) -> bool:
        with self.lock:
            if blk.index <= self.head.index:      return False
            if blk.prev_hash != self.head.hash:   return False
            self.chain.append(blk)
            self.votes.clear()
            return True

    def gossip_payload(self) -> List[dict]:
        with self.lock:
            return [dataclasses.asdict(b) for b in self.chain]

    def load(self, file: pathlib.Path):
        if file.exists():
            with file.open() as f:
                raw = json.load(f)
                self.chain = [Block(**b) for b in raw]

    def save(self, file: pathlib.Path):
        with file.open("w") as f:
            json.dump([dataclasses.asdict(b) for b in self.chain], f)

# ---------- статистика ----------
def exponential_mean(values: List[float], alpha: float = 0.2) -> float:
    if not values: return 0.0
    ema = values[0]
    for v in values[1:]:
        ema = alpha * v + (1 - alpha) * ema
    return ema

# ---------- сеть ----------
def gossip_recv(sock: socket.socket, foreign: dict, stop: threading.Event):
    while not stop.is_set():
        try:
            data, addr = sock.recvfrom(65536)
            foreign[addr] = [Block(**b) for b in json.loads(data)]
        except Exception:
            pass

def gossip_send(sock: socket.socket, chain: LocalChain, peers: List[tuple], stop: threading.Event):
    while not stop.is_set():
        for ip, port in peers:
            try:
                sock.sendto(json.dumps(chain.gossip_payload()).encode(), (ip, port))
            except Exception:
                pass
        time.sleep(GOSSIP_SEC)

# ---------- консенсус ----------
def consensus(chain: LocalChain, foreign: dict) -> Optional[Block]:
    candidates: Dict[str, Block] = {}
    for ch in foreign.values():
        if ch[-1].index > chain.head.index:
            candidates[ch[-1].hash] = ch[-1]
    if not candidates:
        return None
    best = max(candidates, key=lambda h: sum(1 for ch in foreign.values() if ch[-1].hash == h))
    return candidates[best]

# ---------- пчёлы ----------
def bee_simulator(chain: LocalChain, stats_q: queue.Queue, stop: threading.Event):
    role = BeeRole.THIEF if random.random() < chain.cheat_prob else BeeRole.HONEST
    while not stop.is_set():
        time.sleep(BLOCK_SEC)
        nectar = round(random.gauss(0.5, 0.1), 2)
        if role == BeeRole.THIEF:
            nectar *= random.uniform(1.5, 2.5)
        new_block = chain.head.next(chain.node_id, nectar)
        if chain.add(new_block):
            stats_q.put(nectar)

# ---------- принтер ----------
def stats_printer(stats_q: queue.Queue, chain: LocalChain, stop: threading.Event):
    window: List[float] = []
    while not stop.is_set():
        try:
            window.append(stats_q.get(timeout=1))
            if len(window) > WINDOW_MIN:
                window.pop(0)
            ema = exponential_mean(window)
            with chain.lock:
                ln = len(chain.chain)
                print(f"[{time.strftime('%H:%M:%S')}] узел {chain.node_id} "
                      f"блоков {ln} мед/час {ema*120:.1f} кг")
        except queue.Empty:
            pass

# ---------- graceful ----------
stop_event = threading.Event()
def shutdown(sig, frame):
    print("\nСохраняю цепочку и выхожу...")
    stop_event.set()

# ---------- main ----------
def main():
    parser = argparse.ArgumentParser(description="Пчельний блокчейн")
    parser.add_argument("--id",    type=int, required=True, help="ID узла")
    parser.add_argument("--port",  type=int, required=True, help="UDP-порт")
    parser.add_argument("--boot",  required=True, help="ip:port первого узла")
    parser.add_argument("--cheat", type=float, default=0.0, help="доля воров 0..1")
    args = parser.parse_args()

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    file  = pathlib.Path(f"beechain-{args.id}.json")
    chain = LocalChain(args.id, cheat_prob=args.cheat)
    chain.load(file)

    boot_ip, boot_port = args.boot.split(":")
    peers = [(boot_ip, int(boot_port))]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", args.port))

    foreign_chains: dict = {}
    stats_q: queue.Queue[float] = queue.Queue()

    threads = [
        threading.Thread(target=gossip_recv, args=(sock, foreign_chains, stop_event), daemon=True),
        threading.Thread(target=gossip_send, args=(sock, chain, peers, stop_event), daemon=True),
        threading.Thread(target=bee_simulator, args=(chain, stats_q, stop_event), daemon=True),
        threading.Thread(target=stats_printer, args=(stats_q, chain, stop_event), daemon=True),
    ]
    for t in threads: t.start()

    while not stop_event.is_set():
        time.sleep(BLOCK_SEC)
        winner = consensus(chain, foreign_chains)
        if winner and chain.add(winner):
            print("Переключились на более длинную цепочку")

    chain.save(file)
    sock.close()
    print("До встречи, пчёлки!")

# ---------- запуск ----------
if __name__ == "__main__":
    main()

