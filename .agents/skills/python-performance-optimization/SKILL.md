---
name: python-performance-optimization
description: Strategies and patterns for identifying and fixing performance bottlenecks in Python.
---

# Python Performance Optimization ⚡

This skill provides guidance and patterns for improving Python performance in the DesignBox project, with a focus on execution speed, memory usage, and measurable bottlenecks.

## 🔍 Profiling Concepts
- **CPU profiling**: Identify functions that consume the most execution time. Prefer `cProfile` for a first pass.
- **Memory profiling**: Track memory spikes, excessive allocations, and leaks.
- **Line profiling**: Use line-by-line analysis for hot paths when high-level profiling is not specific enough.

## 🚀 Optimization Patterns
- **Comprehensions**: Prefer list and dictionary comprehensions over `for` loops with `append` when they remain readable. They are implemented efficiently in CPython.
- **Generators**: Use generator expressions, such as `(x for x in data)`, to process large datasets without loading everything into memory.
- **String concatenation**: Avoid repeated `s += "text"` inside loops. Use `"".join(parts)` instead.
- **Caching**: Use `functools.lru_cache` for expensive pure functions with repeated inputs.
- **Batch I/O**: Minimize repeated disk, database, or COM calls. Prefer batching when the surrounding API supports it.

## 🛠️ Suggested Tools
1. **cProfile**: Standard Python profiler for CPU time.
2. **functools.lru_cache**: Cache results of expensive deterministic functions.
3. **time.perf_counter**: Lightweight timing for focused code paths.
4. **tracemalloc**: Standard-library memory allocation tracing.
5. **NumPy**: Consider only for heavy numeric operations where vectorization is clear and justified.

## 📝 Best Practices
1. **Profile before optimizing**: Do not guess where the bottleneck is; measure it first.
2. **Focus on hot paths**: Optimize code that runs often or dominates total runtime.
3. **Prefer clarity over micro-optimization**: Do not sacrifice maintainability unless the performance impact is significant and measured.
4. **Use built-ins**: Native Python built-ins are often implemented in C and are usually faster than custom loops.
5. **Validate behavior after optimization**: Add or run tests when changing performance-critical logic.
