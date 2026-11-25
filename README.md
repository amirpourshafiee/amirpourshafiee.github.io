# Amir Pourshafiee — Portfolio Site

This folder is the source for your portfolio site, published at:
https://claude.ai/artifact/6WcySXGHBnnA6XZPuoTvkU

## What's in here

- `index.html` — the whole site. One file: all the HTML, CSS, and JS are
  inline, no build step. Open it directly in a browser to preview changes.
- `assets/` — the photos and the car-detection clip the site uses.
- `tests/test_site.py` — a pytest suite that checks the page for broken
  links, missing images, unbalanced tags, and a handful of facts that
  should (or shouldn't) appear on the page. Run it after any edit:

  ```
  python3 -m pytest tests/test_site.py
  ```

  (needs `pip install pytest` once, if you don't have it)

## Easiest way to make changes

Open this folder in a Claude chat (attach/link this `PersonalWeb` folder)
and just describe what you want changed — a new role, a tweaked bullet, a
different photo, wording, whatever. Claude can edit `index.html` directly
in this folder and re-publish to the same artifact link above, so the live
site updates and the link never changes.

If you'd rather edit by hand: `index.html` is plain HTML, laid out as a
`<style>` block followed by one `<section>` per part of the site
(Experience, Projects, Publications, Skills, Contact). Each role or
project is one `<article>`. Save, open the file in a browser to check it,
then hand it to Claude to publish (editing the file yourself doesn't
update the live artifact link by itself — publishing does).

## Version history

This folder is a local git repo (`git log` to see past states). Commit
after changes you want to keep a record of:

```
git add -A
git commit -m "describe the change"
```
