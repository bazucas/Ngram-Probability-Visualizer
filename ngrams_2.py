import tkinter as tk
from tkinter import font as tkfont, messagebox
import math
import re
import json
import os
from collections import Counter

# ───────────── Translations ─────────────
TR = {
    'pt': dict(
        title='Calculadora de Probabilidades n-grama',
        counts='Contagens carregadas (editáveis)',
        sentence='Frase:',
        ngram='n-grama:',
        smoothing='Alisamento Laplace',
        calc='Calcular',
        expl='Explicação',
        zero_warn='⚠️  Pelo menos um n-grama tem contagem 0 → probabilidade total = 0',
        use_log='Usar log-probabilidades'
    ),
    'en': dict(
        title='N-gram Probability Calculator',
        counts='Loaded counts (editable)',
        sentence='Sentence:',
        ngram='n-gram:',
        smoothing='Laplace smoothing',
        calc='Calculate',
        expl='Explanation',
        zero_warn='⚠️  At least one n-gram has count 0 → total probability = 0',
        use_log='Use log-probabilities'
    ),
    'fr': dict(
        title='Calculateur de probas n-grammes',
        counts='Comptes chargés (modifiable)',
        sentence='Phrase :',
        ngram='n-gramme :',
        smoothing='Lissage Laplace',
        calc='Calculer',
        expl='Explication',
        zero_warn='⚠️  Au moins un n-gramme a une fréquence 0 → probabilité totale = 0',
        use_log='Utiliser log-probas'
    )
}

FLAGS = {'pt': 'PT', 'en': 'EN', 'fr': 'FR'}

# ───────────── Default n-gram counts ─────────────
DEFAULT_COUNTS = {
    1: {  # unigram counts
        '<s>': 6, '</s>': 6, 'a': 1, 'as': 1, 'batatas': 3, 'comer': 1,
        'comida': 1, 'como': 5, 'de': 1, 'eu': 2, 'fritas': 4, 'gosto': 1,
        'homem': 1, 'no': 1, 'não': 2, 'os': 1, 'podes': 1, 'qualquer': 1,
        'relatório': 1, 'saudáveis': 2, 'são': 3, 'toda': 1, 'tu': 1,
        'vegetais': 3, 'vimos': 1
    },
    2: {  # bigram counts
        ("<s>", "como"): 2, ("<s>", "eu"): 1, ("<s>", "não"): 1, ("<s>", "tu"): 1,
        ("<s>", "as"): 1, ("a", "comida"): 1, ("as", "batatas"): 1,
        ("batatas", "fritas"): 3, ("comer", "batatas"): 1,
        ("comida", "</s>"): 2, ("como", "batatas"): 1, ("como", "os"): 1,
        ("como", "qualquer"): 1, ("como", "vegetais"): 1, ("como", "vimos"): 1,
        ("de", "vegetais"): 1, ("eu", "como"): 1, ("eu", "gosto"): 1,
        ("fritas", "como"): 2, ("fritas", "não"): 1, ("fritas", "toda"): 1,
        ("gosto", "de"): 1, ("homem", "são"): 1, ("no", "relatório"): 1,
        ("não", "podes"): 1, ("não", "são"): 1, ("os", "vegetais"): 1,
        ("podes", "comer"): 1, ("qualquer", "homem"): 1, ("relatório", "as"): 1,
        ("saudáveis", "</s>"): 1, ("saudáveis", "eu"): 1, ("são", "</s>"): 1,
        ("são", "saudáveis"): 2, ("toda", "a"): 1, ("tu", "fritas"): 1,
        ("vegetais", "</s>"): 2, ("vegetais", "são"): 1, ("vimos", "no"): 1
    },
    3: {  # trigram counts
        ('<s>', '<s>', 'como'): 2, ('<s>', '<s>', 'eu'): 1, ('<s>', '<s>', 'não'): 1,
        ('<s>', '<s>', 'tu'): 1, ('<s>', '<s>', 'as'): 1,
        ('<s>', 'as', 'batatas'): 1, ('<s>', 'como', 'os'): 1,
        ('<s>', 'como', 'vimos'): 1, ('<s>', 'eu', 'como'): 1,
        ('<s>', 'não', 'podes'): 1, ('<s>', 'tu', 'fritas'): 1,
        ('a', 'comida', '</s>'): 2, ('as', 'batatas', 'fritas'): 1,
        ('batatas', 'fritas', 'como'): 2, ('batatas', 'fritas', 'não'): 1,
        ('comer', 'batatas', 'fritas'): 1, ('como', 'as', 'batatas'): 1,
        ('como', 'batatas', 'fritas'): 1, ('como', 'os', 'vegetais'): 1,
        ('como', 'vegetais', 'são'): 1, ('de', 'vegetais', 'são'): 1,
        ('eu', 'gosto', 'de'): 1, ('fritas', 'não', 'são'): 1,
        ('fritas', 'toda', 'a'): 1, ('gosto', 'de', 'vegetais'): 1,
        ('homem', 'são', 'saudáveis'): 1, ('no', 'relatório', 'as'): 1,
        ('não', 'podes', 'comer'): 1, ('não', 'são', 'saudáveis'): 1,
        ('os', 'vegetais', 'são'): 1, ('podes', 'comer', 'batatas'): 1,
        ('qualquer', 'homem', 'são'): 1, ('relatório', 'as', 'batatas'): 1,
        ('são', 'saudáveis', 'eu'): 1, ('são', 'saudáveis', '</s>'): 1,
        ('toda', 'a', 'comida'): 1, ('tu', 'fritas', 'não'): 1,
        ('vegetais', 'são', 'saudáveis'): 1, ('vimos', 'no', 'relatório'): 1
    }
}

def load_counts(fname='counts.json'):
    """Load optional JSON counts, falling back to defaults."""
    if not os.path.isfile(fname):
        return DEFAULT_COUNTS.copy()
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        out = {}
        for n, d in raw.items():
            n = int(n)
            out[n] = {
                tuple(k.split()) if isinstance(k, str) else tuple(k): v
                for k, v in d.items()
            }
        return {**DEFAULT_COUNTS, **out}
    except Exception as e:
        messagebox.showwarning(
            'JSON',
            f'Error reading {fname}: {e}\nUsing defaults.'
        )
        return DEFAULT_COUNTS.copy()

ALL_COUNTS = load_counts()

class NgramGUI(tk.Tk):
    """Main GUI for n-gram probability calculator."""
    def __init__(self):
        super().__init__()
        self.lang = 'pt'
        self.n_val = tk.IntVar(value=1)
        self.laplace = tk.BooleanVar(value=False)
        self.use_log = tk.BooleanVar(value=True)  # NEW: toggle log vs direct product
        self.font = tkfont.Font(family='Consolas', size=11)
        self._build_ui()
        self._translate()
        self._populate_counts()

    def _build_ui(self):
        top = tk.Frame(self); top.pack(fill='x', padx=6, pady=4)
        # Calculate button
        self.btn_calc = tk.Button(top, text='', command=self._calculate)
        self.btn_calc.pack(side='left')
        # Language selection
        self.lang_var = tk.StringVar(value=FLAGS[self.lang])
        tk.OptionMenu(top, self.lang_var, *FLAGS.values(),
                      command=self._chg_lang).pack(side='right')

        # Options: n-gram order, Laplace smoothing, use log
        opts = tk.Frame(self); opts.pack(fill='x', padx=6)
        self.lbl_ng = tk.Label(opts, text=''); self.lbl_ng.pack(side='left')
        for n in (1, 2, 3):
            tk.Radiobutton(opts, text=str(n), variable=self.n_val,
                           value=n, command=self._populate_counts).pack(side='left')
        # Laplace smoothing checkbox
        self.chk_lap = tk.Checkbutton(opts, text='', variable=self.laplace,
                                      command=self._translate)
        self.chk_lap.pack(side='left')
        # Use log vs direct product checkbox
        self.chk_log = tk.Checkbutton(opts, text='', variable=self.use_log,
                                      command=self._translate)
        self.chk_log.pack(side='left')

        # Counts text area
        self.lbl_counts = tk.Label(self, anchor='w'); self.lbl_counts.pack(fill='x', padx=6)
        self.txt_counts = tk.Text(self, height=12, font=self.font)
        self.txt_counts.pack(fill='both', padx=6)

        # Sentence entry
        sf = tk.Frame(self); sf.pack(fill='x', padx=6, pady=(4,0))
        self.lbl_sent = tk.Label(sf, text=''); self.lbl_sent.pack(side='left')
        self.ent_sent = tk.Entry(sf, font=self.font)
        self.ent_sent.pack(fill='x', expand=True)
        self.ent_sent.insert(0, "não podes comer batatas fritas")

        # Explanation area
        self.lbl_expl = tk.Label(self, anchor='w'); self.lbl_expl.pack(fill='x', padx=6, pady=(8,0))
        self.txt_expl = tk.Text(self, height=14, font=self.font, wrap='none', state='disabled')
        self.txt_expl.pack(fill='both', padx=6, pady=(0,6))

    def _translate(self):
        t = TR[self.lang]
        # Update all UI texts
        self.title(t['title'])
        self.lbl_counts.config(text=t['counts'])
        self.lbl_sent.config(text=t['sentence'])
        self.lbl_ng.config(text=t['ngram'])
        self.chk_lap.config(text=t['smoothing'])
        self.chk_log.config(text=t['use_log'])
        self.btn_calc.config(text=t['calc'])
        self.lbl_expl.config(text=t['expl'])

    def _chg_lang(self, *_):
        self.lang = {v:k for k,v in FLAGS.items()}[self.lang_var.get()]
        self._translate()

    def _populate_counts(self, *_):
        """Fill the counts textbox with current n-gram counts."""
        n = self.n_val.get()
        counts = ALL_COUNTS[n]
        lines = []
        if n == 1:
            for tok, c in sorted(counts.items(), key=lambda x:(-x[1],x[0])):
                lines.append(f"{tok}\t{c}")
        else:
            for gram, c in sorted(counts.items(), key=lambda x:(-x[1],x[0])):
                lines.append(f"{' '.join(gram)}\t{c}")
        self.txt_counts.delete('1.0','end')
        self.txt_counts.insert('end', "\n".join(lines) + "\n")

    def _parse_counts(self, n):
        """Read user-edited counts from the text widget."""
        counts = Counter()
        for ln in self.txt_counts.get('1.0','end').splitlines():
            parts = re.split(r'\s+', ln.strip())
            if len(parts)<2: continue
            *tokens, num = parts
            if len(tokens)!=n: continue
            try:
                cnt = int(num)
            except ValueError:
                continue
            counts[tuple(tokens)] += cnt
        if not counts:
            counts.update(ALL_COUNTS[n])
        return counts

    def _calculate(self):
        """Compute and display n-gram probabilities (Laplace optional, log vs product)."""
        n = self.n_val.get()
        sentence = self.ent_sent.get().strip().lower()
        if not sentence:
            messagebox.showerror("Error","Empty sentence.")
            return

        tokens = sentence.split()
        counts = self._parse_counts(n)
        vocab = {tok for gram in counts for tok in gram}
        V = len(vocab)

        # Prepare sequence with padding
        seq = ['<s>']*(n-1) + tokens + ['</s>']
        explanation = []
        zero_prob = False

        # Choose start index so we skip initial <s><s> for trigrams
        start = (n-1) if n!=3 else n

        # Initialize for product or log-sum
        product = 1.0
        logp = 0.0

        for i in range(start, len(seq)):
            gram = tuple(seq[i-n+1 : i+1])
            prefix = gram[:-1]
            num = counts[gram]
            den = sum(c for k,c in counts.items() if k[:-1]==prefix)

            # Handle missing prefix → zero probability
            if den == 0:
                p = 0.0
            else:
                if self.laplace.get():
                    num += 1
                    den += V
                p = num / den

            # Record formula for UI
            explanation.append(f"P({gram[-1]} | {' '.join(gram[:-1])}) = {num}/{den} = {p:.6f}")

            if p == 0.0:
                zero_prob = True

            # Accumulate product and log-prob
            product *= p
            if p > 0.0:
                logp += math.log(p)

        # After loop, show results
        explanation.append("")
        if zero_prob and not self.laplace.get():
            explanation.append(TR[self.lang]['zero_warn'])
            final_prob = 0.0
        else:
            if self.use_log.get():
                # show log-sum and exp
                explanation.append("Log-prob = " + " + ".join(f"log({p:.6f})"
                                                       for p in [math.log(cnt/den)
                                                              if den>0 else float('-inf')
                                                              for (_,_,_), cnt, den in []]))
                # we already have logp
                explanation.append(f"= {logp:.6f}")
                final_prob = math.exp(logp)
            else:
                # direct product
                explanation.append(f"Product = {product:.8e}")
                final_prob = product

        explanation.append(f"Probability = {final_prob:.8e}")

        # Display in UI
        self.txt_expl.config(state='normal')
        self.txt_expl.delete('1.0','end')
        self.txt_expl.insert('end', "\n".join(explanation))
        self.txt_expl.config(state='disabled')


if __name__=='__main__':
    NgramGUI().mainloop()
