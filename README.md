# Sarkaz Translator

A cipher tool for the Sarkaz script in *Arknights: Endfield*.

## Cipher

**Encryption:** Fully functional. Converts Chinese text into Sarkaz letter strings using modular arithmetic.

**Decryption:** Extremely limited. The decoder can only match a very small subset of in-game proper nouns (character names, place names, etc.). It is practically unable to translate full sentences.

## How It Works

Each Chinese character is mapped to a letter via:

```
Letter = REMAINDER_MAP[ord(Chinese_Character) % 56]
```

Because multiple characters share the same remainder, decoding is one-to-many — each letter maps back to a set of candidates, making full sentence recovery infeasible without a comprehensive game dictionary.

## Usage

Double-click `Sarkaz.bat` to run.

No dependencies beyond the Python standard library.
