# Stable Portfolio URLs Instead of Randomized Encryption

## Problem

The portfolio application originally used AES-128-CBC with a random IV
for `project_id`.

Conceptually:

``` php
$iv = openssl_random_pseudo_bytes(16);
$encrypted = openssl_encrypt(
    $id,
    'AES-128-CBC',
    $this->key,
    OPENSSL_RAW_DATA,
    $iv
);
```

Because the IV was random, encrypting the same database ID repeatedly
produced different ciphertext.

``` text
Project 45
→ Random IV A → URL A

Project 45
→ Random IV B → URL B

Project 45
→ Random IV C → URL C
```

## Why It Matters

Crawlers operate on URLs. If one project appears at thousands of
different URLs, crawlers can treat them as separate resources.

It also reduces URL-based cache reuse because each URL creates a
different cache key.

## Investigation

The crawler analysis found approximately:

``` text
144,713 unique encrypted project_id values
```

The values were decrypted with the application's existing decryption
implementation.

The result was:

``` text
144,713 encrypted values
→ 50 actual project IDs
```

All 50 actual IDs existed in the database.

So the huge URL count represented the same small set of portfolio
projects.

## Find URL Generation

``` bash
grep -Rni --include='*.php' 'portfolio-details\.php' /home/zawadulkawum/htdocs/zawadulkawum

grep -Rni --include='*.php' '\$crypt->encrypt' /home/zawadulkawum/htdocs/zawadulkawum
```

The URL generation was found in application files such as `index.php`
and `layouts/sidebar_portfolio.php`.

## Solution

Use a stable, deterministic public identifier for every project.

Required properties:

-   Same project produces the same identifier.
-   Raw sequential database IDs are not exposed directly.
-   Identifier is URL-safe.
-   Identifier remains stable.
-   The same project maps to one canonical URL.

Example:

``` text
project_id=APK9qmR1BQ-5s-8teR_CQuA
```

The exact scheme can vary, but it must be deterministic.

## Result

Before:

``` text
One project → many random URLs
```

After:

``` text
One project → one stable public URL
```

This improves crawler behavior, caching, indexing, analytics, sharing,
and long-term URL stability.

## Lesson

Encryption is not automatically a good URL identifier. Evaluate URL
identifiers for stability, uniqueness, URL safety, enumeration
resistance, cache behavior, and canonicalization.
