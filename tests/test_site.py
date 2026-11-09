"""Content and safety checks for the portfolio page."""
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

HTML = (Path(__file__).parent.parent / "index.html").read_text(encoding="utf-8")
VOID = {"meta", "link", "br", "img", "hr", "input"}


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.ids, self.hrefs, self.text = [], [], [], []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a":
            self.hrefs.append(attrs.get("href", ""))
        if tag in ("style", "script"):
            self.skip += 1
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        assert self.stack and self.stack[-1] == tag, f"bad nesting at </{tag}>"
        self.stack.pop()
        if tag in ("style", "script"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.text.append(data)


@pytest.fixture(scope="module")
def page():
    c = Collector()
    c.feed(HTML)
    return c


def test_tags_balance(page):
    assert page.stack == []


def test_no_em_dashes():
    assert "\u2014" not in HTML and "&mdash;" not in HTML


@pytest.mark.parametrize("private", ["882-7336", "Newark", "94560"])
def test_private_details_stay_off_the_page(private):
    assert private not in HTML


def test_dropped_stale_copy_from_old_site():
    assert "great opening" not in HTML


def test_in_page_links_resolve(page):
    for href in page.hrefs:
        if href.startswith("#"):
            assert href[1:] in page.ids


def test_only_allowed_external_hosts():
    hosts = set(re.findall(r'(?:href|src)="https://([^/"]+)', HTML))
    assert hosts <= {"fonts.googleapis.com", "fonts.gstatic.com", "www.linkedin.com", "search.proquest.com", "arc.aiaa.org", "www.udacity.com", "www.coursera.org", "trialtrue.itch.io"}


@pytest.mark.parametrize(
    "fact",
    ["kappa", "14", "120 hours", "Super Leaper", "SIERRA-B", "AIAA SciTech", "Walle"],
)
def test_key_facts_present(page, fact):
    text = " ".join(page.text) + HTML
    assert fact.lower() in text.lower() or fact == "kappa" and "&kappa;" in HTML


def test_every_color_token_has_a_light_default():
    root = re.search(r":root \{(.*?)\}", HTML, re.S).group(1)
    defined = set(re.findall(r"--[\w-]+(?=:)", root))
    assert set(re.findall(r"var\((--[\w-]+)", HTML)) <= defined


def test_images_exist_and_have_alt():
    root = Path(__file__).parent.parent
    imgs = re.findall(r"<img\b[^>]*>", HTML)
    assert len(imgs) >= 6
    for tag in imgs:
        src = re.search(r'src="([^"]+)"', tag).group(1)
        assert (root / src).is_file(), src
        assert re.search(r'alt="[^"]{10,}"', tag), src


def test_rover_writeup_recovered():
    for fact in [
        "rocker-bogie", "D* Lite", "Haar cascade", "30 kg", "Geoff Budd",
        "May 8", "WPI", "wheel pivot servo", "camera misalignment", "OPERS",
    ]:
        assert fact in HTML


def test_rover_award_is_accurate():
    # The team received a real NASA Technology Achievement Award (confirmed
    # in Amir's own resume slides and the project poster), but the Final
    # Report shows the competition run itself was a partial result, not a
    # win. Both facts should be on the page together, not the old
    # "won a technology achievement prize" phrasing, which implied the
    # award was for winning the challenge outright.
    assert "Technology Achievement Award" in HTML
    assert "won a technology achievement prize" not in HTML


def test_new_projects_recovered():
    for fact in [
        "Automated Cell Identification Device", "ACID", "nano-injection",
        "SIERRA-B UAS", "fluxgate magnetometer", "laser altimeter",
    ]:
        assert fact in HTML


def test_internship_photos_present():
    root = Path(__file__).parent.parent
    for src in ["assets/pearl-camera.jpg", "assets/nasa-uas-intern.jpg", "assets/canrig-plc.jpg"]:
        assert (root / src).is_file(), src
        assert src in HTML


def test_nanodegree_project_images_present():
    # Real output screenshots pulled from Amir's own completed workspaces
    # (confirmed via his restored, ~5-year-old notebook files on Udacity):
    # predicted facial keypoints on a Course 1 test image, and two actual
    # generated captions (one correct, one wrong) from the Course 3
    # Image Captioning inference notebook.
    root = Path(__file__).parent.parent
    for src in ["assets/keypoints-detection.jpg", "assets/captioning-surf.jpg", "assets/captioning-miss.jpg"]:
        assert (root / src).is_file(), src
        assert src in HTML
    for fact in [
        "a man on a surfboard riding a wave in the ocean",
        "a vase of flowers sitting on top of a table",
    ]:
        assert fact in HTML


def test_udacity_certificate_verified():
    # Only the Computer Vision Nanodegree was actually completed (graduated,
    # Feb 2021, confirmed via Udacity's dashboard and certificate page). The
    # other 7 enrollments on the account are 0-63% complete and shouldn't be
    # claimed as credentials.
    assert "udacity.com/certificate/e/df7675c8-43d1-11eb-bc8f-c7aa982877fe" in HTML
    assert "Affectiva" in HTML and "NVIDIA Deep Learning Institute" in HTML


def test_nanodegree_projects_present():
    # The Computer Vision Nanodegree curriculum (confirmed live on Amir's
    # Udacity account: nd891, Course 1 and Course 3) had two graded
    # capstone projects, both marked Complete. Both should be on the page.
    for fact in ["Facial Keypoint Detection", "Image Captioning"]:
        assert fact in HTML


def test_game_dev_project_is_a_one_liner():
    # Demoted from a full feature article (with gallery images) to a
    # single text-only entry: thematically off-brand for a staff
    # perception/test portfolio, so it shouldn't carry the same visual
    # weight as the robotics and CV work.
    for fact in ["Space Blaster", "StairWars", "trialtrue.itch.io/retro-2d-shooter", "trialtrue.itch.io/stairwars"]:
        assert fact in HTML
    for src in ["assets/shooter-gameplay.jpg", "assets/stairwars-title.jpg", "assets/stairwars-gameplay.jpg"]:
        assert src not in HTML


def test_coursera_certificates_verified():
    # Verified via Amir's Coursera certificates page (My Learning >
    # Certificates): Generative AI with LLMs (DeepLearning.AI / AWS, Jul
    # 2024); Claude Code: Software Engineering with Generative AI Agents
    # (Vanderbilt, Apr 2026). The Game Design and Development 1/2 certs
    # are intentionally left off the Certificates line (content revision
    # pass): they dilute by association next to the CV Nanodegree and
    # the DeepLearning.AI course, for a staff perception/test audience.
    for code in ["RBGXG6D3CEQ3", "GXL4WUHIU3MA"]:
        assert f"coursera.org/account/accomplishments/verify/{code}" in HTML
    for code in ["UHH290Y28LL0", "1Y0MSM2HN3OQ"]:
        assert f"coursera.org/account/accomplishments/verify/{code}" not in HTML


def test_llm_labs_described():
    # Confirmed via Amir's Coursera course page for Generative AI with LLMs:
    # three graded labs (Week 1-3), each marked Submitted, Grade: 100%. The
    # lab notebooks themselves are locked (Coursera/AWS expire lab access
    # after a window), so there are no real output screenshots to pull,
    # unlike the Udacity nanodegree project images above.
    for fact in ["zero, one, and few-shot", "LoRA", "PPO", "FLAN-T5"]:
        assert fact in HTML


def test_resume_cross_check_additions_present():
    # Confirmed via Amir's own resume (AmirPourshafiee_Resume_Nov2026.pdf):
    # three facts that were on the resume but missing from the site, added
    # in the resume cross-check pass.
    for fact in [
        "2 Android XR devices and a Galaxy XR",
        "Led triage of customer software feedback, managing and presenting weekly reports to the executive leadership team",
        "Imatest",
    ]:
        assert fact in HTML


def test_self_description_is_not_plain_test_engineer():
    # Per explicit request: Amir's own professional label (meta description,
    # hero lede, status line) should read "verification and validation",
    # not plain "test engineer". This leaves untouched: the SDET job title
    # (a real, historical title), "test automation"/"test cases"/"test
    # coverage" as technical terms, and "6 test engineers" (someone else's
    # title, not Amir's).
    assert "staff test engineer" not in HTML.lower()
    assert "verification and validation" in HTML.lower()
    assert "Software Development Engineer in Test, Computer Vision" in HTML


def test_google_role_is_not_on_assignment_phrasing():
    # Amir has since left Magic Leap, so the contract relationship with
    # Google no longer needs the employer-mandated "on assignment at
    # Google" phrasing. Per explicit request, it now reads as a TVC
    # (Google's own term for vendor contract staff) via Magic Leap.
    assert "on assignment at Google" not in HTML
    assert "Google (TVC via Magic Leap)" in HTML


def test_video_assets_exist_and_stay_small():
    root = Path(__file__).parent.parent
    for src in re.findall(r'(?:src|poster)="(assets/car-detection\.[a-z0-9]+)"', HTML):
        assert (root / src).is_file(), src
    assert (root / "assets/car-detection.mp4").stat().st_size < 3_000_000
    assert re.search(r"<video[^>]*\bmuted\b[^>]*\bplaysinline\b", HTML)
