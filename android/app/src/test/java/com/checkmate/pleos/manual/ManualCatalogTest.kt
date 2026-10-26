package com.checkmate.pleos.manual

import org.junit.Assert.*
import org.junit.Test
import java.net.URI

class ManualCatalogTest {
    @Test fun missingAndUnknownProfilesNeverSelectAReplacement() {
        assertNull(ManualCatalog.find(null))
        assertNull(ManualCatalog.find("ioniq5-2024-us"))
    }

    @Test fun sourcesMatchTheirProfileScope() {
        assertEquals(ManualCatalog.profiles.size, ManualCatalog.profiles.map { it.id }.distinct().size)
        ManualCatalog.profiles.forEach { profile ->
            val url = URI(profile.source.url)
            assertEquals("https", url.scheme)
            assertEquals("ownersmanual.hyundai.com", url.host)
            assertTrue(url.path.contains("/${profile.projectCode}/${profile.modelYear}/ko_KR/"))
            assertTrue(profile.source.contentSha256.matches(Regex("[a-f0-9]{64}")))
        }
    }
}
