"""CLR-Synth: build certified curriculum chains of hidden rules from a data domain.

A domain provides records, value universes with one-sentence descriptions, and a library of published lists. For
each of the four levels the pipeline draws a hidden class C, picks the example A, three members m0, m1, m2, a practice
non-member n_p, and seven test non-members N_t, and certifies the class with four probes: Known (clrsynth screen),
Hidden (P0), Learnable (P1), and Solvable (P1H)."""
