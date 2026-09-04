#[inline(always)]
unsafe fn load_data_avx2(
    x: &mut [__m256i; 8],
    ms: &mut MsgSchedule,
    t2: &mut RoundStates,
    data: *const __m128i,
) {
    #[allow(non_snake_case)]
    let MASK = _mm256_set_epi64x(
        0x0809_0A0B_0C0D_0E0F_i64,
        0x0001_0203_0405_0607_i64,
        0x0809_0A0B_0C0D_0E0F_i64,
        0x0001_0203_0405_0607_i64,
    );

    macro_rules! unrolled_iterations {
        ($($i:literal),*) => {$(
            x[$i] = _mm256_insertf128_si256(x[$i], _mm_loadu_si128(data.add(8 + $i) as *const _), 1);
            x[$i] = _mm256_insertf128_si256(x[$i], _mm_loadu_si128(data.add($i) as *const _), 0);

            x[$i] = _mm256_shuffle_epi8(x[$i], MASK);

            let t = _mm_loadu_si128(K64.as_ptr().add($i * 2) as *const u64 as *const _);
            let y = _mm256_add_epi64(x[$i], _mm256_set_m128i(t, t));

            _mm_store_si128(
                &mut ms[2 * $i] as *mut u64 as *mut _,
                _mm256_extracti128_si256(y, 0),
            );
            _mm_store_si128(
                &mut t2[2 * $i] as *mut u64 as *mut _,
                _mm256_extracti128_si256(y, 1),
            );
        )*};
    }

    unrolled_iterations!(0, 1, 2, 3, 4, 5, 6, 7);
}
