# 

SOMA Programming Idioms and Best Practices

SOMA v1.1 Language Specification - Programming Style Guide

Category: Tutorial

## Date: 24 November 2025

Introduction

### SOMA uses execution scope not lexical scope

The Core Principle

## Blocks execute with fresh Registers without automatic access to parent scope Understanding Lexical vs Execution Scope

Wrong assumption in SOMA

```
Does not work - assuming lexical scope
42 !_.x
{{ _.x >toString }}
```

Correct approach with context passing

```
Works correctly - explicit context passing
42 !_.x
_.
>{{ !_. _.x >toString }}
```

## 

Summary

