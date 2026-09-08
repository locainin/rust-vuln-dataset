fn matches_caret(cmp: &Comparator, ver: &Version) -> bool {
    if ver.major != cmp.major {
        return false;
    }

    let Some(minor) = cmp.minor else {
        return true;
    };

    let Some(patch) = cmp.patch else {
        if cmp.major > 0 {
            return ver.minor >= minor;
        } else {
            return ver.minor == minor;
        }
    };

    if cmp.major > 0 {
        if ver.minor != minor {
            return ver.minor > minor;
        } else if ver.patch != patch {
            return ver.patch > patch;
        }
    } else if minor > 0 {
        if ver.minor != minor {
            return false;
        } else if ver.patch != patch {
            return ver.patch > patch;
        }
    } else if ver.minor != minor || ver.patch != patch {
        return false;
    }

    ver.pre >= cmp.pre
}
