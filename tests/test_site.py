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
    assert hosts <= {"fonts.googleapis.com", "fonts.gstatic.com", "www.linkedin.com", "search.proquest.com", "arc.aiaa.org", "www.udacity.com", "www.coursera.org", "trialtrue.itch.io", "github.com"}


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
    # Confirmed via Amir's own resume (AmirPourshafiee_Resume_Nov2026.pdf),
    # resume cross-check pass. "Led triage of customer software feedback..."
    # was dropped in the Nov 2026 showcase rewrite (see
    # test_experience_is_one_title_free_entry) along with the other
    # corporate-process bullets, so it's no longer asserted here.
    for fact in [
        "Samsung Galaxy XR, Xreal Aura, and an Android XR reference design",
        "Imatest",
    ]:
        assert fact in HTML
    # Dropped per the Nov 2026 resume update: team-size/device numbers changed
    # (12 milestones, 21 defects, 5-person team), and the old standalone
    # weekly-regression-runs bullet was folded into the team-validation bullet.
    assert "managing and presenting weekly reports" not in HTML
    assert "2 Android XR devices and a Galaxy XR" not in HTML


def test_experience_is_one_title_free_entry():
    # Per explicit request (Nov 2026 showcase rewrite): the site should read
    # as a place to show work, not a job-hunt resume. The four Magic
    # Leap/Google role entries (each with its own job-title headline) were
    # collapsed into one company entry with no title at all, and the
    # org-chart-flavored bullets ("reporting to...", "presenting weekly
    # reports to the executive leadership team") were cut.
    for title in [
        "Staff Software Engineer, QA",
        "Staff Software Engineer, Software Quality",
        "Senior Software Engineer, Perception Quality",
        "Software Development Engineer in Test, Computer Vision",
    ]:
        assert title not in HTML
    assert "staff test engineer" not in HTML.lower()
    assert "verification and validation engineer" not in HTML.lower()
    assert "Led triage of customer software feedback" not in HTML
    assert "reporting to the senior director" not in HTML
    assert HTML.count('<article class="role">') == 1
    assert "<h3>Magic Leap</h3>" in HTML


def test_google_collaboration_is_plain_language():
    # The old "Google (TVC via Magic Leap)" HR phrasing, and the separate
    # Google role entry it lived in, are both gone now that the whole
    # tenure is one Magic Leap entry; the collaboration is one plain
    # sentence instead of an employment-structure label.
    assert "on assignment at Google" not in HTML
    assert "Google (TVC via Magic Leap)" not in HTML
    assert "embedded with Google's Android XR team" in HTML


def test_hero_lede_is_builder_voice_not_job_title():
    # Per explicit request: the hero introduces what Amir builds, not a
    # job title, so the page doesn't read as a job application.
    assert "Staff verification and validation engineer" not in HTML
    assert "I build and test perception systems" in HTML


def test_vio_regression_harness_present():
    # Added per explicit request: Amir's vioreg / vio-regress project, confirmed
    # live on its GitHub repo page (README) on 2026-11-14, with fault-injection
    # stress-test numbers added from the Nov 2026 resume update.
    for fact in [
        "github.com/amirpourshafiee/vio-regress",
        "EuRoC", "OpenVINS", "Cohen's kappa",
        "RPE", "ATE", "thresholds.yaml",
        "45 injected faults", "caught 2 of 5 fault types",
    ]:
        assert fact in HTML


def test_google_assignment_numbers_match_nov_2026_resume():
    # Team size, milestone count, and defect count updated per the Nov 2026
    # resume (previously 5 milestones / 14 defects with no stated team size).
    for fact in ["5-person", "12", "21", "release-blocking defects"]:
        assert fact in HTML
    assert "Surfaced <span class=\"good\">14</span>" not in HTML


def test_vio_regression_diagram_is_accessible_svg():
    assert '<svg viewBox="0 0 900 320"' in HTML
    assert 'role="img"' in HTML
    match = re.search(r'<svg\b[^>]*aria-label="([^"]{20,})"', HTML)
    assert match, "diagram svg should carry a descriptive aria-label"


def test_mutagent_project_present():
    # Added per explicit request: Amir's mutagent project, an LLM
    # test-generation agent graded by mutation testing rather than line
    # coverage, added 2026-11-19.
    for fact in [
        "github.com/amirpourshafiee/mutagent",
        "mutation testing",
        "8 modules",
        "coverage-guided agent",
        "Claude Sonnet 5.5",
        "7 of 8",
        "81% to 97%",
    ]:
        assert fact in HTML


def test_claimcheck_project_present():
    # Added per explicit request: Amir's claimcheck project, a citation and
    # hallucination checker for AI answers, confirmed live on its GitHub
    # repo page (README) on 2026-11-24.
    for fact in [
        "github.com/amirpourshafiee/claimcheck",
        "F1 0.89", "0.74", "76-claim", "13 of 72",
    ]:
        assert fact in HTML


def test_video_assets_exist_and_stay_small():
    root = Path(__file__).parent.parent
    for src in re.findall(r'(?:src|poster)="(assets/car-detection\.[a-z0-9]+)"', HTML):
        assert (root / src).is_file(), src
    assert (root / "assets/car-detection.mp4").stat().st_size < 3_000_000
    assert re.search(r"<video[^>]*\bmuted\b[^>]*\bplaysinline\b", HTML)


def test_snugcad_card_has_video_and_honest_limits():
    # The SnugCAD card embeds the rover demo with controls and no autoplay
    # (the file is about 9 MB), and states the limits shown in the video.
    root = Path(__file__).parent.parent
    for src in ["assets/snugcad-rover.mp4", "assets/snugcad-rover.jpg"]:
        assert (root / src).is_file(), src
        assert src in HTML
    tag = re.search(r"<video[^>]*snugcad-rover\.mp4[^>]*>", HTML).group(0)
    assert "controls" in tag and 'preload="none"' in tag and "autoplay" not in tag
    for fact in ["SnugCAD", "URDF (Unified Robot Description Format)", "placeholder blocks", "nothing on the rover has been printed"]:
        assert fact in HTML
