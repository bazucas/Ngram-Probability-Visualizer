import tkinter as tk
from tkinter import font as tkfont, messagebox
import math, re, json, os
from collections import Counter

# ─────────────  Translations  ─────────────
TR = {
    'pt': dict(title='Calculadora de Probabilidades n-grama',
               counts='Contagens carregadas (editáveis)',
               sentence='Frase:', ngram='n-grama:',
               smoothing='Alisamento Laplace',
               calc='Calcular', expl='Explicação',
               zero_warn='⚠️  Pelo menos um n-grama tem contagem 0 → probabilidade total = 0'),
    'en': dict(title='N-gram Probability Calculator',
               counts='Loaded counts (editable)',
               sentence='Sentence:', ngram='n-gram:',
               smoothing='Laplace smoothing',
               calc='Calculate', expl='Explanation',
               zero_warn='⚠️  At least one n-gram has count 0 → total probability = 0'),
    'fr': dict(title='Calculateur de probas n-grammes',
               counts='Comptes chargés (modifiable)',
               sentence='Phrase :', ngram='n-gramme :',
               smoothing='Lissage Laplace',
               calc='Calculer', expl='Explication',
               zero_warn='⚠️  Au moins un n-gramme a une fréquence 0 → probabilité totale = 0')
}

FLAGS = {'pt': 'PT', 'en': 'EN', 'fr': 'FR'}

# ─────────────  Default Counts  ─────────────
DEFAULT_COUNTS = {
    1: {  # unigrams
        '<s>': 6, '</s>': 6, 'a': 1, 'as': 1, 'batatas': 3, 'comer': 1, 'comida': 1,
        'como': 5, 'de': 1, 'eu': 2, 'fritas': 4, 'gosto': 1, 'homem': 1, 'no': 1,
        'não': 2, 'os': 1, 'podes': 1, 'qualquer': 1, 'relatório': 1,
        'saudáveis': 2, 'são': 3, 'toda': 1, 'tu': 1, 'vegetais': 3, 'vimos': 1
    },
    2: {  # bigrams
        ("<s>", "como"): 2, ("<s>", "eu"): 1, ("<s>", "não"): 1, ("<s>", "tu"): 1, ("<s>", "as"): 1,
        ("a", "comida"): 1, ("as", "batatas"): 1, ("batatas", "fritas"): 3, ("comer", "batatas"): 1,
        ("comida", "</s>"): 2, ("como", "batatas"): 1, ("como", "os"): 1, ("como", "qualquer"): 1,
        ("como", "vegetais"): 1, ("como", "vimos"): 1, ("de", "vegetais"): 1, ("eu", "como"): 1,
        ("eu", "gosto"): 1, ("fritas", "como"): 2, ("fritas", "não"): 1, ("fritas", "toda"): 1,
        ("gosto", "de"): 1, ("homem", "são"): 1, ("no", "relatório"): 1, ("não", "podes"): 1,
        ("não", "são"): 1, ("os", "vegetais"): 1, ("podes", "comer"): 1, ("qualquer", "homem"): 1,
        ("relatório", "as"): 1, ("saudáveis", "</s>"): 1, ("saudáveis", "eu"): 1, ("são", "</s>"): 1,
        ("são", "saudáveis"): 2, ("toda", "a"): 1, ("tu", "fritas"): 1, ("vegetais", "</s>"): 2,
        ("vegetais", "são"): 1, ("vimos", "no"): 1
    },
    3: {  # trigrams
        ('<s>', '<s>', 'como'): 2, ('<s>', '<s>', 'eu'): 1, ('<s>', '<s>', 'não'): 1,
        ('<s>', '<s>', 'tu'): 1, ('<s>', '<s>', 'as'): 1, ('<s>', 'as', 'batatas'): 1,
        ('<s>', 'como', 'os'): 1, ('<s>', 'como', 'vimos'): 1, ('<s>', 'eu', 'como'): 1,
        ('<s>', 'não', 'podes'): 1, ('<s>', 'tu', 'fritas'): 1, ('a', 'comida', '</s>'): 2,
        ('as', 'batatas', 'fritas'): 1, ('batatas', 'fritas', 'como'): 2, ('batatas', 'fritas', 'não'): 1,
        ('comer', 'batatas', 'fritas'): 1, ('como', 'as', 'batatas'): 1, ('como', 'batatas', 'fritas'): 1,
        ('como', 'os', 'vegetais'): 1, ('como', 'vegetais', 'são'): 1, ('de', 'vegetais', 'são'): 1,
        ('eu', 'gosto', 'de'): 1, ('fritas', 'não', 'são'): 1, ('fritas', 'toda', 'a'): 1,
        ('gosto', 'de', 'vegetais'): 1, ('homem', 'são', 'saudáveis'): 1, ('no', 'relatório', 'as'): 1,
        ('não', 'podes', 'comer'): 1, ('não', 'são', 'saudáveis'): 1, ('os', 'vegetais', 'são'): 1,
        ('podes', 'comer', 'batatas'): 1, ('qualquer', 'homem', 'são'): 1, ('relatório', 'as', 'batatas'): 1,
        ('são', 'saudáveis', 'eu'): 1, ('são', 'saudáveis', '</s>'): 1, ('toda', 'a', 'comida'): 1,
        ('tu', 'fritas', 'não'): 1, ('vegetais', 'são', 'saudáveis'): 1, ('vimos', 'no', 'relatório'): 1
    }
}

# ─────────────  Optional JSON Loading  ─────────────
def load_counts(fname='counts.json'):
    if not os.path.isfile(fname):
        return DEFAULT_COUNTS.copy()
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        out = {}
        for n, d in raw.items():
            n = int(n)
            out[n] = {tuple(k.split()) if isinstance(k, str) else tuple(k): v
                      for k, v in d.items()}
        return {**DEFAULT_COUNTS, **out}
    except Exception as e:
        messagebox.showwarning('JSON', f'Error reading {fname}: {e}\nUsing defaults.')
        return DEFAULT_COUNTS.copy()

ALL_COUNTS = load_counts()

# ─────────────  GUI  ─────────────
class NgramGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang = 'pt'
        self.n_val = tk.IntVar(value=1)
        self.laplace = tk.BooleanVar(value=False)
        self.font_m = tkfont.Font(family='Consolas', size=11)
        self._build()
        self._translate()
        self._populate_counts()

    def _build(self):
        top = tk.Frame(self); top.pack(fill='x', padx=6, pady=4)
        self.btn_calc = tk.Button(top, command=self._calculate); self.btn_calc.pack(side='left')
        self.lang_var = tk.StringVar(value=FLAGS[self.lang])
        tk.OptionMenu(top, self.lang_var, *FLAGS.values(), command=self._chg_lang).pack(side='right')

        opts = tk.Frame(self); opts.pack(fill='x', padx=6)
        self.lbl_ng = tk.Label(opts); self.lbl_ng.pack(side='left')
        for n in (1, 2, 3):
            tk.Radiobutton(opts, text=str(n), variable=self.n_val, value=n,
                           command=self._populate_counts).pack(side='left')
        tk.Checkbutton(opts, variable=self.laplace, command=self._translate).pack(side='left')
        self.chk_lbl = tk.Label(opts); self.chk_lbl.pack(side='left', padx=(0, 10))

        self.lbl_counts = tk.Label(self, anchor='w'); self.lbl_counts.pack(fill='x', padx=6)
        self.txt_counts = tk.Text(self, height=12, font=self.font_m)
        self.txt_counts.pack(fill='both', expand=False, padx=6)

        sf = tk.Frame(self); sf.pack(fill='x', padx=6, pady=(4, 0))
        self.lbl_sent = tk.Label(sf); self.lbl_sent.pack(side='left')
        self.ent_sent = tk.Entry(sf, font=self.font_m)
        self.ent_sent.pack(fill='x', expand=True)
        self.ent_sent.insert(0, "não podes comer batatas fritas")

        self.lbl_expl = tk.Label(self, anchor='w'); self.lbl_expl.pack(fill='x', padx=6, pady=(8, 0))
        self.txt_expl = tk.Text(self, height=14, font=self.font_m, wrap='none', state='disabled')
        self.txt_expl.pack(fill='both', expand=True, padx=6, pady=(0, 6))

    def _translate(self):
        t = TR[self.lang]
        self.title(t['title'])
        self.lbl_counts.config(text=t['counts'])
        self.lbl_sent.config(text=t['sentence'])
        self.lbl_ng.config(text=t['ngram'])
        self.chk_lbl.config(text=t['smoothing'])
        self.btn_calc.config(text=t['calc'])
        self.lbl_expl.config(text=t['expl'])

    def _chg_lang(self, *_):
        self.lang = {v: k for k, v in FLAGS.items()}[self.lang_var.get()]
        self._translate()

    def _populate_counts(self, *_):
        n = self.n_val.get()
        counts = ALL_COUNTS[n]
        lines = []
        if n == 1:
            for tok, c in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
                lines.append(f"{tok}\t{c}")
        else:
            for gram, c in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
                lines.append(f"{' '.join(gram)}\t{c}")
        self.txt_counts.delete('1.0', 'end')
        self.txt_counts.insert('end', "\n".join(lines) + "\n")

    def _parse_counts(self, n):
        counts = Counter()
        for ln in self.txt_counts.get('1.0', 'end').splitlines():
            ln = ln.strip()
            if not ln:
                continue
            *tokens, c = re.split(r'\s+', ln)
            try:
                cnt = int(c)
            except ValueError:
                continue
            if len(tokens) != n:
                continue
            counts[tuple(tokens)] += cnt
        if not counts:
            counts.update(ALL_COUNTS[n])
        return counts

    def _calculate(self):
        n = self.n_val.get()
        sent_raw = self.ent_sent.get().strip().lower()
        if not sent_raw:
            messagebox.showerror("Error", "Empty sentence.")
            return
        tokens = sent_raw.split()
        counts = self._parse_counts(n)
        vocab = {tok for gram in counts for tok in gram}
        V = len(vocab)

        sent = ['<s>'] * (n - 1) + tokens + ['</s>']
        terms = []
        logp = 0.0
        zero_prob = False  # 🆕 flag

        explanation = []

        for i in range(n - 1, len(sent)):
            gram = tuple(sent[i - n + 1:i + 1])
            prefix = gram[:-1]
            num = counts[gram]
            den = sum(c for k, c in counts.items() if k[:-1] == prefix)

            # For missing bigrams and trigrams, assign 0 probability without raising error
            if den == 0 and n == 2:
                p = 0.0
            elif den == 0 and n == 3:
                p = 0.0
            else:
                if self.laplace.get():
                    num += 1
                    den += V
                p = num / den

            formula = f"P({gram[-1]} | {' '.join(gram[:-1])}) = {num}/{den} = {p:.6f}"
            explanation.append(formula)

            if p == 0.0:
                zero_prob = True
                terms.append((gram, num, den, 0.0))
            else:
                logp += math.log(p)
                terms.append((gram, num, den, p))

        explanation.append("")
        if zero_prob and not self.laplace.get():
            explanation.append(TR[self.lang]['zero_warn'])
            prob = 0.0
        else:
            explanation.append("Log-prob = " + " + ".join(
                f"log({t[3]:.6f})" for t in terms if t[3] > 0))
            explanation.append(f"= {logp:.6f}")
            prob = math.exp(logp)
        explanation.append(f"Probability = {prob:.8e}")

        self.txt_expl.config(state='normal')
        self.txt_expl.delete('1.0', 'end')
        self.txt_expl.insert('end', "\n".join(explanation))
        self.txt_expl.config(state='disabled')


if __name__ == '__main__':
    NgramGUI().mainloop()
