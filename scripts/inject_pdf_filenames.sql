-- =============================================================================
-- inject_pdf_filenames.sql
-- Injecte les anciens noms de fichiers PDF dans rentReceipts.pdfFilename
--
-- Ancien format : {cp}-{bien}-{unit}[-{chambre}].{YYYY-MM}.{type}.pdf
-- Correspondance :
--   QuittanceLoyer    → paid=1
--   AvisEcheance      → paid=0
--   QuittanceGarantie → joint via rentReceiptsDetail (description='Garantie')
--
-- Avant exécution, vérifier les noms en base :
--   SELECT id, name, zipCode FROM places;
--   SELECT u.id, u.name, u.friendlyName, p.name place FROM placesUnits u JOIN places p ON u.placeId=p.id;
--   SELECT r.id, r.name, u.name unit FROM placesUnitsRooms r JOIN placesUnits u ON r.placesUnitsId=u.id;
-- =============================================================================

START TRANSACTION;

-- =============================================================================
-- PLACE : 59000 - Mexico
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Aptn1 — colocation, chambres "1" et "2"
-- -----------------------------------------------------------------------------

-- Aptn1 / chambre "1" — QuittanceLoyer (paid=1)
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '2024-10' THEN '59000-Mexico-Aptn1-1.2024-10.QuittanceLoyer.pdf'
  WHEN '2024-11' THEN '59000-Mexico-Aptn1-1.2024-11.QuittanceLoyer.pdf'
  WHEN '2024-12' THEN '59000-Mexico-Aptn1-1.2024-12.QuittanceLoyer.pdf'
  WHEN '2025-01' THEN '59000-Mexico-Aptn1-1.2025-01.QuittanceLoyer.pdf'
  WHEN '2025-02' THEN '59000-Mexico-Aptn1-1.2025-02.QuittanceLoyer.pdf'
  WHEN '2025-03' THEN '59000-Mexico-Aptn1-1.2025-03.QuittanceLoyer.pdf'
  WHEN '2025-04' THEN '59000-Mexico-Aptn1-1.2025-04.QuittanceLoyer.pdf'
  WHEN '2025-05' THEN '59000-Mexico-Aptn1-1.2025-05.QuittanceLoyer.pdf'
  WHEN '2025-06' THEN '59000-Mexico-Aptn1-1.2025-06.QuittanceLoyer.pdf'
  WHEN '2025-07' THEN '59000-Mexico-Aptn1-1.2025-07.QuittanceLoyer.pdf'
  WHEN '2025-08' THEN '59000-Mexico-Aptn1-1.2025-08.QuittanceLoyer.pdf'
  WHEN '2025-09' THEN '59000-Mexico-Aptn1-1.2025-09.QuittanceLoyer.pdf'
  WHEN '2025-10' THEN '59000-Mexico-Aptn1-1.2025-10.QuittanceLoyer.pdf'
  WHEN '2025-11' THEN '59000-Mexico-Aptn1-1.2025-11.QuittanceLoyer.pdf'
  WHEN '2025-12' THEN '59000-Mexico-Aptn1-1.2025-12.QuittanceLoyer.pdf'
  WHEN '2026-01' THEN '59000-Mexico-Aptn1-1.2026-01.QuittanceLoyer.pdf'
  WHEN '2026-02' THEN '59000-Mexico-Aptn1-1.2026-02.QuittanceLoyer.pdf'
  WHEN '2026-03' THEN '59000-Mexico-Aptn1-1.2026-03.QuittanceLoyer.pdf'
  WHEN '2026-04' THEN '59000-Mexico-Aptn1-1.2026-04.QuittanceLoyer.pdf'
END
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Aptn1' OR u.friendlyName = 'Aptn1')
  AND room.name = '1'
  AND r.paid = 1
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN (
    '2024-10','2024-11','2024-12',
    '2025-01','2025-02','2025-03','2025-04','2025-05','2025-06',
    '2025-07','2025-08','2025-09','2025-10','2025-11','2025-12',
    '2026-01','2026-02','2026-03','2026-04'
  );

-- Aptn1 / chambre "2" — QuittanceLoyer (paid=1)
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '2024-09' THEN '59000-Mexico-Aptn1-2.2024-09.QuittanceLoyer.pdf'
  WHEN '2024-10' THEN '59000-Mexico-Aptn1-2.2024-10.QuittanceLoyer.pdf'
  WHEN '2024-11' THEN '59000-Mexico-Aptn1-2.2024-11.QuittanceLoyer.pdf'
  WHEN '2024-12' THEN '59000-Mexico-Aptn1-2.2024-12.QuittanceLoyer.pdf'
  WHEN '2025-01' THEN '59000-Mexico-Aptn1-2.2025-01.QuittanceLoyer.pdf'
  WHEN '2025-02' THEN '59000-Mexico-Aptn1-2.2025-02.QuittanceLoyer.pdf'
  WHEN '2025-03' THEN '59000-Mexico-Aptn1-2.2025-03.QuittanceLoyer.pdf'
  WHEN '2025-04' THEN '59000-Mexico-Aptn1-2.2025-04.QuittanceLoyer.pdf'
  WHEN '2025-05' THEN '59000-Mexico-Aptn1-2.2025-05.QuittanceLoyer.pdf'
  WHEN '2025-06' THEN '59000-Mexico-Aptn1-2.2025-06.QuittanceLoyer.pdf'
  WHEN '2025-07' THEN '59000-Mexico-Aptn1-2.2025-07.QuittanceLoyer.pdf'
  WHEN '2025-08' THEN '59000-Mexico-Aptn1-2.2025-08.QuittanceLoyer.pdf'
  WHEN '2025-09' THEN '59000-Mexico-Aptn1-2.2025-09.QuittanceLoyer.pdf'
  WHEN '2025-10' THEN '59000-Mexico-Aptn1-2.2025-10.QuittanceLoyer.pdf'
  WHEN '2025-11' THEN '59000-Mexico-Aptn1-2.2025-11.QuittanceLoyer.pdf'
  WHEN '2025-12' THEN '59000-Mexico-Aptn1-2.2025-12.QuittanceLoyer.pdf'
  WHEN '2026-01' THEN '59000-Mexico-Aptn1-2.2026-01.QuittanceLoyer.pdf'
  WHEN '2026-02' THEN '59000-Mexico-Aptn1-2.2026-02.QuittanceLoyer.pdf'
  WHEN '2026-03' THEN '59000-Mexico-Aptn1-2.2026-03.QuittanceLoyer.pdf'
  WHEN '2026-04' THEN '59000-Mexico-Aptn1-2.2026-04.QuittanceLoyer.pdf'
END
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Aptn1' OR u.friendlyName = 'Aptn1')
  AND room.name = '2'
  AND r.paid = 1
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN (
    '2024-09','2024-10','2024-11','2024-12',
    '2025-01','2025-02','2025-03','2025-04','2025-05','2025-06',
    '2025-07','2025-08','2025-09','2025-10','2025-11','2025-12',
    '2026-01','2026-02','2026-03','2026-04'
  );

-- -----------------------------------------------------------------------------
-- Aptn3 — non-colocation (pas de chambre)
-- -----------------------------------------------------------------------------

-- Aptn3 — QuittanceLoyer (paid=1) — pas de 2025-07
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '2024-09' THEN '59000-Mexico-Aptn3.2024-09.QuittanceLoyer.pdf'
  WHEN '2024-10' THEN '59000-Mexico-Aptn3.2024-10.QuittanceLoyer.pdf'
  WHEN '2024-11' THEN '59000-Mexico-Aptn3.2024-11.QuittanceLoyer.pdf'
  WHEN '2024-12' THEN '59000-Mexico-Aptn3.2024-12.QuittanceLoyer.pdf'
  WHEN '2025-01' THEN '59000-Mexico-Aptn3.2025-01.QuittanceLoyer.pdf'
  WHEN '2025-02' THEN '59000-Mexico-Aptn3.2025-02.QuittanceLoyer.pdf'
  WHEN '2025-03' THEN '59000-Mexico-Aptn3.2025-03.QuittanceLoyer.pdf'
  WHEN '2025-04' THEN '59000-Mexico-Aptn3.2025-04.QuittanceLoyer.pdf'
  WHEN '2025-05' THEN '59000-Mexico-Aptn3.2025-05.QuittanceLoyer.pdf'
  WHEN '2025-06' THEN '59000-Mexico-Aptn3.2025-06.QuittanceLoyer.pdf'
  WHEN '2025-08' THEN '59000-Mexico-Aptn3.2025-08.QuittanceLoyer.pdf'
  WHEN '2025-09' THEN '59000-Mexico-Aptn3.2025-09.QuittanceLoyer.pdf'
  WHEN '2025-10' THEN '59000-Mexico-Aptn3.2025-10.QuittanceLoyer.pdf'
  WHEN '2025-11' THEN '59000-Mexico-Aptn3.2025-11.QuittanceLoyer.pdf'
  WHEN '2025-12' THEN '59000-Mexico-Aptn3.2025-12.QuittanceLoyer.pdf'
  WHEN '2026-01' THEN '59000-Mexico-Aptn3.2026-01.QuittanceLoyer.pdf'
  WHEN '2026-02' THEN '59000-Mexico-Aptn3.2026-02.QuittanceLoyer.pdf'
  WHEN '2026-03' THEN '59000-Mexico-Aptn3.2026-03.QuittanceLoyer.pdf'
  WHEN '2026-04' THEN '59000-Mexico-Aptn3.2026-04.QuittanceLoyer.pdf'
END
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Aptn3' OR u.friendlyName = 'Aptn3')
  AND r.placeUnitRoomId IS NULL
  AND r.paid = 1
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN (
    '2024-09','2024-10','2024-11','2024-12',
    '2025-01','2025-02','2025-03','2025-04','2025-05','2025-06',
    '2025-08','2025-09','2025-10','2025-11','2025-12',
    '2026-01','2026-02','2026-03','2026-04'
  );

-- Aptn3 — QuittanceGarantie (2025-08)
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN rentReceiptsDetail d ON d.rentReceiptsId = r.id AND d.description = 'Garantie'
SET r.pdfFilename = '59000-Mexico-Aptn3.2025-08.QuittanceGarantie.pdf'
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Aptn3' OR u.friendlyName = 'Aptn3')
  AND r.placeUnitRoomId IS NULL
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') = '2025-08';

-- -----------------------------------------------------------------------------
-- Aptn4 — colocation, chambres Ch1, Ch2, Ch3, Ch4
-- -----------------------------------------------------------------------------

-- Aptn4 / Ch1 — QuittanceLoyer (paid=1) — gap 2025-05 à 2025-08
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '2024-09' THEN '59000-Mexico-Aptn4-Ch1.2024-09.QuittanceLoyer.pdf'
  WHEN '2024-10' THEN '59000-Mexico-Aptn4-Ch1.2024-10.QuittanceLoyer.pdf'
  WHEN '2024-11' THEN '59000-Mexico-Aptn4-Ch1.2024-11.QuittanceLoyer.pdf'
  WHEN '2024-12' THEN '59000-Mexico-Aptn4-Ch1.2024-12.QuittanceLoyer.pdf'
  WHEN '2025-01' THEN '59000-Mexico-Aptn4-Ch1.2025-01.QuittanceLoyer.pdf'
  WHEN '2025-02' THEN '59000-Mexico-Aptn4-Ch1.2025-02.QuittanceLoyer.pdf'
  WHEN '2025-03' THEN '59000-Mexico-Aptn4-Ch1.2025-03.QuittanceLoyer.pdf'
  WHEN '2025-04' THEN '59000-Mexico-Aptn4-Ch1.2025-04.QuittanceLoyer.pdf'
  WHEN '2025-09' THEN '59000-Mexico-Aptn4-Ch1.2025-09.QuittanceLoyer.pdf'
  WHEN '2025-10' THEN '59000-Mexico-Aptn4-Ch1.2025-10.QuittanceLoyer.pdf'
  WHEN '2025-11' THEN '59000-Mexico-Aptn4-Ch1.2025-11.QuittanceLoyer.pdf'
  WHEN '2025-12' THEN '59000-Mexico-Aptn4-Ch1.2025-12.QuittanceLoyer.pdf'
  WHEN '2026-01' THEN '59000-Mexico-Aptn4-Ch1.2026-01.QuittanceLoyer.pdf'
  WHEN '2026-02' THEN '59000-Mexico-Aptn4-Ch1.2026-02.QuittanceLoyer.pdf'
  WHEN '2026-03' THEN '59000-Mexico-Aptn4-Ch1.2026-03.QuittanceLoyer.pdf'
  WHEN '2026-04' THEN '59000-Mexico-Aptn4-Ch1.2026-04.QuittanceLoyer.pdf'
END
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Aptn4' OR u.friendlyName = 'Aptn4')
  AND room.name = 'Ch1'
  AND r.paid = 1
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN (
    '2024-09','2024-10','2024-11','2024-12',
    '2025-01','2025-02','2025-03','2025-04',
    '2025-09','2025-10','2025-11','2025-12',
    '2026-01','2026-02','2026-03','2026-04'
  );

-- Aptn4 / Ch1 — AvisEcheance (paid=0)
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '2024-09' THEN '59000-Mexico-Aptn4-Ch1.2024-09.AvisEcheance.pdf'
  WHEN '2024-10' THEN '59000-Mexico-Aptn4-Ch1.2024-10.AvisEcheance.pdf'
  WHEN '2024-11' THEN '59000-Mexico-Aptn4-Ch1.2024-11.AvisEcheance.pdf'
END
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Aptn4' OR u.friendlyName = 'Aptn4')
  AND room.name = 'Ch1'
  AND r.paid = 0
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN ('2024-09','2024-10','2024-11');

-- Aptn4 / Ch1 — QuittanceGarantie (3 locataires distincts : 2024-09, 2024-10, 2025-09)
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
  INNER JOIN rentReceiptsDetail d ON d.rentReceiptsId = r.id AND d.description = 'Garantie'
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '2024-09' THEN '59000-Mexico-Aptn4-Ch1.2024-09.QuittanceGarantie.pdf'
  WHEN '2024-10' THEN '59000-Mexico-Aptn4-Ch1.2024-10.QuittanceGarantie.pdf'
  WHEN '2025-09' THEN '59000-Mexico-Aptn4-Ch1.2025-09.QuittanceGarantie.pdf'
END
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Aptn4' OR u.friendlyName = 'Aptn4')
  AND room.name = 'Ch1'
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN ('2024-09','2024-10','2025-09');

-- Aptn4 / Ch2 — QuittanceLoyer (paid=1) — gap 2025-05
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '2024-09' THEN '59000-Mexico-Aptn4-Ch2.2024-09.QuittanceLoyer.pdf'
  WHEN '2024-10' THEN '59000-Mexico-Aptn4-Ch2.2024-10.QuittanceLoyer.pdf'
  WHEN '2024-11' THEN '59000-Mexico-Aptn4-Ch2.2024-11.QuittanceLoyer.pdf'
  WHEN '2024-12' THEN '59000-Mexico-Aptn4-Ch2.2024-12.QuittanceLoyer.pdf'
  WHEN '2025-01' THEN '59000-Mexico-Aptn4-Ch2.2025-01.QuittanceLoyer.pdf'
  WHEN '2025-02' THEN '59000-Mexico-Aptn4-Ch2.2025-02.QuittanceLoyer.pdf'
  WHEN '2025-03' THEN '59000-Mexico-Aptn4-Ch2.2025-03.QuittanceLoyer.pdf'
  WHEN '2025-04' THEN '59000-Mexico-Aptn4-Ch2.2025-04.QuittanceLoyer.pdf'
  WHEN '2025-06' THEN '59000-Mexico-Aptn4-Ch2.2025-06.QuittanceLoyer.pdf'
  WHEN '2025-07' THEN '59000-Mexico-Aptn4-Ch2.2025-07.QuittanceLoyer.pdf'
  WHEN '2025-08' THEN '59000-Mexico-Aptn4-Ch2.2025-08.QuittanceLoyer.pdf'
  WHEN '2025-09' THEN '59000-Mexico-Aptn4-Ch2.2025-09.QuittanceLoyer.pdf'
  WHEN '2025-10' THEN '59000-Mexico-Aptn4-Ch2.2025-10.QuittanceLoyer.pdf'
  WHEN '2025-11' THEN '59000-Mexico-Aptn4-Ch2.2025-11.QuittanceLoyer.pdf'
  WHEN '2025-12' THEN '59000-Mexico-Aptn4-Ch2.2025-12.QuittanceLoyer.pdf'
  WHEN '2026-01' THEN '59000-Mexico-Aptn4-Ch2.2026-01.QuittanceLoyer.pdf'
  WHEN '2026-02' THEN '59000-Mexico-Aptn4-Ch2.2026-02.QuittanceLoyer.pdf'
  WHEN '2026-03' THEN '59000-Mexico-Aptn4-Ch2.2026-03.QuittanceLoyer.pdf'
  WHEN '2026-04' THEN '59000-Mexico-Aptn4-Ch2.2026-04.QuittanceLoyer.pdf'
END
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Aptn4' OR u.friendlyName = 'Aptn4')
  AND room.name = 'Ch2'
  AND r.paid = 1
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN (
    '2024-09','2024-10','2024-11','2024-12',
    '2025-01','2025-02','2025-03','2025-04',
    '2025-06','2025-07','2025-08','2025-09','2025-10','2025-11','2025-12',
    '2026-01','2026-02','2026-03','2026-04'
  );

-- Aptn4 / Ch2 — QuittanceGarantie (2025-06)
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
  INNER JOIN rentReceiptsDetail d ON d.rentReceiptsId = r.id AND d.description = 'Garantie'
SET r.pdfFilename = '59000-Mexico-Aptn4-Ch2.2025-06.QuittanceGarantie.pdf'
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Aptn4' OR u.friendlyName = 'Aptn4')
  AND room.name = 'Ch2'
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') = '2025-06';

-- Aptn4 / Ch3 — QuittanceLoyer (paid=1) — gap 2025-07 et 2025-08
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '2024-09' THEN '59000-Mexico-Aptn4-Ch3.2024-09.QuittanceLoyer.pdf'
  WHEN '2024-10' THEN '59000-Mexico-Aptn4-Ch3.2024-10.QuittanceLoyer.pdf'
  WHEN '2024-11' THEN '59000-Mexico-Aptn4-Ch3.2024-11.QuittanceLoyer.pdf'
  WHEN '2024-12' THEN '59000-Mexico-Aptn4-Ch3.2024-12.QuittanceLoyer.pdf'
  WHEN '2025-01' THEN '59000-Mexico-Aptn4-Ch3.2025-01.QuittanceLoyer.pdf'
  WHEN '2025-02' THEN '59000-Mexico-Aptn4-Ch3.2025-02.QuittanceLoyer.pdf'
  WHEN '2025-03' THEN '59000-Mexico-Aptn4-Ch3.2025-03.QuittanceLoyer.pdf'
  WHEN '2025-04' THEN '59000-Mexico-Aptn4-Ch3.2025-04.QuittanceLoyer.pdf'
  WHEN '2025-05' THEN '59000-Mexico-Aptn4-Ch3.2025-05.QuittanceLoyer.pdf'
  WHEN '2025-06' THEN '59000-Mexico-Aptn4-Ch3.2025-06.QuittanceLoyer.pdf'
  WHEN '2025-09' THEN '59000-Mexico-Aptn4-Ch3.2025-09.QuittanceLoyer.pdf'
  WHEN '2025-10' THEN '59000-Mexico-Aptn4-Ch3.2025-10.QuittanceLoyer.pdf'
  WHEN '2025-11' THEN '59000-Mexico-Aptn4-Ch3.2025-11.QuittanceLoyer.pdf'
  WHEN '2025-12' THEN '59000-Mexico-Aptn4-Ch3.2025-12.QuittanceLoyer.pdf'
  WHEN '2026-01' THEN '59000-Mexico-Aptn4-Ch3.2026-01.QuittanceLoyer.pdf'
  WHEN '2026-02' THEN '59000-Mexico-Aptn4-Ch3.2026-02.QuittanceLoyer.pdf'
  WHEN '2026-03' THEN '59000-Mexico-Aptn4-Ch3.2026-03.QuittanceLoyer.pdf'
  WHEN '2026-04' THEN '59000-Mexico-Aptn4-Ch3.2026-04.QuittanceLoyer.pdf'
END
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Aptn4' OR u.friendlyName = 'Aptn4')
  AND room.name = 'Ch3'
  AND r.paid = 1
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN (
    '2024-09','2024-10','2024-11','2024-12',
    '2025-01','2025-02','2025-03','2025-04','2025-05','2025-06',
    '2025-09','2025-10','2025-11','2025-12',
    '2026-01','2026-02','2026-03','2026-04'
  );

-- Aptn4 / Ch3 — QuittanceGarantie (2025-09 et 2026-04)
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
  INNER JOIN rentReceiptsDetail d ON d.rentReceiptsId = r.id AND d.description = 'Garantie'
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '2025-09' THEN '59000-Mexico-Aptn4-Ch3.2025-09.QuittanceGarantie.pdf'
  WHEN '2026-04' THEN '59000-Mexico-Aptn4-Ch3.2026-04.QuittanceGarantie.pdf'
END
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Aptn4' OR u.friendlyName = 'Aptn4')
  AND room.name = 'Ch3'
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN ('2025-09','2026-04');

-- Aptn4 / Ch4 — QuittanceLoyer (paid=1) — 2024-09 à 2026-04 continu
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '2024-09' THEN '59000-Mexico-Aptn4-Ch4.2024-09.QuittanceLoyer.pdf'
  WHEN '2024-10' THEN '59000-Mexico-Aptn4-Ch4.2024-10.QuittanceLoyer.pdf'
  WHEN '2024-11' THEN '59000-Mexico-Aptn4-Ch4.2024-11.QuittanceLoyer.pdf'
  WHEN '2024-12' THEN '59000-Mexico-Aptn4-Ch4.2024-12.QuittanceLoyer.pdf'
  WHEN '2025-01' THEN '59000-Mexico-Aptn4-Ch4.2025-01.QuittanceLoyer.pdf'
  WHEN '2025-02' THEN '59000-Mexico-Aptn4-Ch4.2025-02.QuittanceLoyer.pdf'
  WHEN '2025-03' THEN '59000-Mexico-Aptn4-Ch4.2025-03.QuittanceLoyer.pdf'
  WHEN '2025-04' THEN '59000-Mexico-Aptn4-Ch4.2025-04.QuittanceLoyer.pdf'
  WHEN '2025-05' THEN '59000-Mexico-Aptn4-Ch4.2025-05.QuittanceLoyer.pdf'
  WHEN '2025-06' THEN '59000-Mexico-Aptn4-Ch4.2025-06.QuittanceLoyer.pdf'
  WHEN '2025-07' THEN '59000-Mexico-Aptn4-Ch4.2025-07.QuittanceLoyer.pdf'
  WHEN '2025-08' THEN '59000-Mexico-Aptn4-Ch4.2025-08.QuittanceLoyer.pdf'
  WHEN '2025-09' THEN '59000-Mexico-Aptn4-Ch4.2025-09.QuittanceLoyer.pdf'
  WHEN '2025-10' THEN '59000-Mexico-Aptn4-Ch4.2025-10.QuittanceLoyer.pdf'
  WHEN '2025-11' THEN '59000-Mexico-Aptn4-Ch4.2025-11.QuittanceLoyer.pdf'
  WHEN '2025-12' THEN '59000-Mexico-Aptn4-Ch4.2025-12.QuittanceLoyer.pdf'
  WHEN '2026-01' THEN '59000-Mexico-Aptn4-Ch4.2026-01.QuittanceLoyer.pdf'
  WHEN '2026-02' THEN '59000-Mexico-Aptn4-Ch4.2026-02.QuittanceLoyer.pdf'
  WHEN '2026-03' THEN '59000-Mexico-Aptn4-Ch4.2026-03.QuittanceLoyer.pdf'
  WHEN '2026-04' THEN '59000-Mexico-Aptn4-Ch4.2026-04.QuittanceLoyer.pdf'
END
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Aptn4' OR u.friendlyName = 'Aptn4')
  AND room.name = 'Ch4'
  AND r.paid = 1
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN (
    '2024-09','2024-10','2024-11','2024-12',
    '2025-01','2025-02','2025-03','2025-04','2025-05','2025-06',
    '2025-07','2025-08','2025-09','2025-10','2025-11','2025-12',
    '2026-01','2026-02','2026-03','2026-04'
  );

-- -----------------------------------------------------------------------------
-- Maison — colocation, chambres Ch1, Ch2, Ch3
-- -----------------------------------------------------------------------------

-- Maison / Ch1 — QuittanceLoyer (paid=1) — gap 2025-08 et 2025-09
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '2024-09' THEN '59000-Mexico-Maison-Ch1.2024-09.QuittanceLoyer.pdf'
  WHEN '2024-10' THEN '59000-Mexico-Maison-Ch1.2024-10.QuittanceLoyer.pdf'
  WHEN '2024-11' THEN '59000-Mexico-Maison-Ch1.2024-11.QuittanceLoyer.pdf'
  WHEN '2024-12' THEN '59000-Mexico-Maison-Ch1.2024-12.QuittanceLoyer.pdf'
  WHEN '2025-01' THEN '59000-Mexico-Maison-Ch1.2025-01.QuittanceLoyer.pdf'
  WHEN '2025-02' THEN '59000-Mexico-Maison-Ch1.2025-02.QuittanceLoyer.pdf'
  WHEN '2025-03' THEN '59000-Mexico-Maison-Ch1.2025-03.QuittanceLoyer.pdf'
  WHEN '2025-04' THEN '59000-Mexico-Maison-Ch1.2025-04.QuittanceLoyer.pdf'
  WHEN '2025-05' THEN '59000-Mexico-Maison-Ch1.2025-05.QuittanceLoyer.pdf'
  WHEN '2025-06' THEN '59000-Mexico-Maison-Ch1.2025-06.QuittanceLoyer.pdf'
  WHEN '2025-07' THEN '59000-Mexico-Maison-Ch1.2025-07.QuittanceLoyer.pdf'
  WHEN '2025-10' THEN '59000-Mexico-Maison-Ch1.2025-10.QuittanceLoyer.pdf'
  WHEN '2025-11' THEN '59000-Mexico-Maison-Ch1.2025-11.QuittanceLoyer.pdf'
  WHEN '2025-12' THEN '59000-Mexico-Maison-Ch1.2025-12.QuittanceLoyer.pdf'
  WHEN '2026-01' THEN '59000-Mexico-Maison-Ch1.2026-01.QuittanceLoyer.pdf'
  WHEN '2026-02' THEN '59000-Mexico-Maison-Ch1.2026-02.QuittanceLoyer.pdf'
  WHEN '2026-03' THEN '59000-Mexico-Maison-Ch1.2026-03.QuittanceLoyer.pdf'
  WHEN '2026-04' THEN '59000-Mexico-Maison-Ch1.2026-04.QuittanceLoyer.pdf'
END
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Maison' OR u.friendlyName = 'Maison')
  AND room.name = 'Ch1'
  AND r.paid = 1
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN (
    '2024-09','2024-10','2024-11','2024-12',
    '2025-01','2025-02','2025-03','2025-04','2025-05','2025-06','2025-07',
    '2025-10','2025-11','2025-12',
    '2026-01','2026-02','2026-03','2026-04'
  );

-- Maison / Ch1 — QuittanceGarantie (2025-10)
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
  INNER JOIN rentReceiptsDetail d ON d.rentReceiptsId = r.id AND d.description = 'Garantie'
SET r.pdfFilename = '59000-Mexico-Maison-Ch1.2025-10.QuittanceGarantie.pdf'
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Maison' OR u.friendlyName = 'Maison')
  AND room.name = 'Ch1'
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') = '2025-10';

-- Maison / Ch2 — QuittanceLoyer (paid=1) — gap 2025-09
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '2024-09' THEN '59000-Mexico-Maison-Ch2.2024-09.QuittanceLoyer.pdf'
  WHEN '2024-10' THEN '59000-Mexico-Maison-Ch2.2024-10.QuittanceLoyer.pdf'
  WHEN '2024-11' THEN '59000-Mexico-Maison-Ch2.2024-11.QuittanceLoyer.pdf'
  WHEN '2024-12' THEN '59000-Mexico-Maison-Ch2.2024-12.QuittanceLoyer.pdf'
  WHEN '2025-01' THEN '59000-Mexico-Maison-Ch2.2025-01.QuittanceLoyer.pdf'
  WHEN '2025-02' THEN '59000-Mexico-Maison-Ch2.2025-02.QuittanceLoyer.pdf'
  WHEN '2025-03' THEN '59000-Mexico-Maison-Ch2.2025-03.QuittanceLoyer.pdf'
  WHEN '2025-04' THEN '59000-Mexico-Maison-Ch2.2025-04.QuittanceLoyer.pdf'
  WHEN '2025-05' THEN '59000-Mexico-Maison-Ch2.2025-05.QuittanceLoyer.pdf'
  WHEN '2025-06' THEN '59000-Mexico-Maison-Ch2.2025-06.QuittanceLoyer.pdf'
  WHEN '2025-07' THEN '59000-Mexico-Maison-Ch2.2025-07.QuittanceLoyer.pdf'
  WHEN '2025-08' THEN '59000-Mexico-Maison-Ch2.2025-08.QuittanceLoyer.pdf'
  WHEN '2025-10' THEN '59000-Mexico-Maison-Ch2.2025-10.QuittanceLoyer.pdf'
  WHEN '2025-11' THEN '59000-Mexico-Maison-Ch2.2025-11.QuittanceLoyer.pdf'
  WHEN '2025-12' THEN '59000-Mexico-Maison-Ch2.2025-12.QuittanceLoyer.pdf'
  WHEN '2026-01' THEN '59000-Mexico-Maison-Ch2.2026-01.QuittanceLoyer.pdf'
  WHEN '2026-02' THEN '59000-Mexico-Maison-Ch2.2026-02.QuittanceLoyer.pdf'
  WHEN '2026-03' THEN '59000-Mexico-Maison-Ch2.2026-03.QuittanceLoyer.pdf'
  WHEN '2026-04' THEN '59000-Mexico-Maison-Ch2.2026-04.QuittanceLoyer.pdf'
END
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Maison' OR u.friendlyName = 'Maison')
  AND room.name = 'Ch2'
  AND r.paid = 1
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN (
    '2024-09','2024-10','2024-11','2024-12',
    '2025-01','2025-02','2025-03','2025-04','2025-05','2025-06','2025-07','2025-08',
    '2025-10','2025-11','2025-12',
    '2026-01','2026-02','2026-03','2026-04'
  );

-- Maison / Ch2 — QuittanceGarantie (2025-10)
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
  INNER JOIN rentReceiptsDetail d ON d.rentReceiptsId = r.id AND d.description = 'Garantie'
SET r.pdfFilename = '59000-Mexico-Maison-Ch2.2025-10.QuittanceGarantie.pdf'
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Maison' OR u.friendlyName = 'Maison')
  AND room.name = 'Ch2'
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') = '2025-10';

-- Maison / Ch3 — QuittanceLoyer (paid=1) — inclut 1970-01, gap 2025-09
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '1970-01' THEN '59000-Mexico-Maison-Ch3.1970-01.QuittanceLoyer.pdf'
  WHEN '2024-09' THEN '59000-Mexico-Maison-Ch3.2024-09.QuittanceLoyer.pdf'
  WHEN '2024-10' THEN '59000-Mexico-Maison-Ch3.2024-10.QuittanceLoyer.pdf'
  WHEN '2024-11' THEN '59000-Mexico-Maison-Ch3.2024-11.QuittanceLoyer.pdf'
  WHEN '2024-12' THEN '59000-Mexico-Maison-Ch3.2024-12.QuittanceLoyer.pdf'
  WHEN '2025-01' THEN '59000-Mexico-Maison-Ch3.2025-01.QuittanceLoyer.pdf'
  WHEN '2025-02' THEN '59000-Mexico-Maison-Ch3.2025-02.QuittanceLoyer.pdf'
  WHEN '2025-03' THEN '59000-Mexico-Maison-Ch3.2025-03.QuittanceLoyer.pdf'
  WHEN '2025-04' THEN '59000-Mexico-Maison-Ch3.2025-04.QuittanceLoyer.pdf'
  WHEN '2025-05' THEN '59000-Mexico-Maison-Ch3.2025-05.QuittanceLoyer.pdf'
  WHEN '2025-06' THEN '59000-Mexico-Maison-Ch3.2025-06.QuittanceLoyer.pdf'
  WHEN '2025-07' THEN '59000-Mexico-Maison-Ch3.2025-07.QuittanceLoyer.pdf'
  WHEN '2025-08' THEN '59000-Mexico-Maison-Ch3.2025-08.QuittanceLoyer.pdf'
  WHEN '2025-10' THEN '59000-Mexico-Maison-Ch3.2025-10.QuittanceLoyer.pdf'
  WHEN '2025-11' THEN '59000-Mexico-Maison-Ch3.2025-11.QuittanceLoyer.pdf'
  WHEN '2025-12' THEN '59000-Mexico-Maison-Ch3.2025-12.QuittanceLoyer.pdf'
  WHEN '2026-01' THEN '59000-Mexico-Maison-Ch3.2026-01.QuittanceLoyer.pdf'
  WHEN '2026-02' THEN '59000-Mexico-Maison-Ch3.2026-02.QuittanceLoyer.pdf'
  WHEN '2026-03' THEN '59000-Mexico-Maison-Ch3.2026-03.QuittanceLoyer.pdf'
  WHEN '2026-04' THEN '59000-Mexico-Maison-Ch3.2026-04.QuittanceLoyer.pdf'
END
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Maison' OR u.friendlyName = 'Maison')
  AND room.name = 'Ch3'
  AND r.paid = 1
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN (
    '1970-01',
    '2024-09','2024-10','2024-11','2024-12',
    '2025-01','2025-02','2025-03','2025-04','2025-05','2025-06','2025-07','2025-08',
    '2025-10','2025-11','2025-12',
    '2026-01','2026-02','2026-03','2026-04'
  );

-- Maison / Ch3 — QuittanceGarantie (2025-10)
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
  INNER JOIN placesUnitsRooms room ON r.placeUnitRoomId = room.id
  INNER JOIN rentReceiptsDetail d ON d.rentReceiptsId = r.id AND d.description = 'Garantie'
SET r.pdfFilename = '59000-Mexico-Maison-Ch3.2025-10.QuittanceGarantie.pdf'
WHERE p.zipCode = 59000
  AND p.name LIKE '%Mexico%'
  AND (u.name = 'Maison' OR u.friendlyName = 'Maison')
  AND room.name = 'Ch3'
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') = '2025-10';

-- =============================================================================
-- PLACE : 59112 - Léon Blum
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Appartement — non-colocation
-- -----------------------------------------------------------------------------

-- Appartement — QuittanceLoyer (paid=1) — 2023-05 à 2026-04 continu
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '2023-05' THEN '59112-LeonBlum-Appartement.2023-05.QuittanceLoyer.pdf'
  WHEN '2023-06' THEN '59112-LeonBlum-Appartement.2023-06.QuittanceLoyer.pdf'
  WHEN '2023-07' THEN '59112-LeonBlum-Appartement.2023-07.QuittanceLoyer.pdf'
  WHEN '2023-08' THEN '59112-LeonBlum-Appartement.2023-08.QuittanceLoyer.pdf'
  WHEN '2023-09' THEN '59112-LeonBlum-Appartement.2023-09.QuittanceLoyer.pdf'
  WHEN '2023-10' THEN '59112-LeonBlum-Appartement.2023-10.QuittanceLoyer.pdf'
  WHEN '2023-11' THEN '59112-LeonBlum-Appartement.2023-11.QuittanceLoyer.pdf'
  WHEN '2023-12' THEN '59112-LeonBlum-Appartement.2023-12.QuittanceLoyer.pdf'
  WHEN '2024-01' THEN '59112-LeonBlum-Appartement.2024-01.QuittanceLoyer.pdf'
  WHEN '2024-02' THEN '59112-LeonBlum-Appartement.2024-02.QuittanceLoyer.pdf'
  WHEN '2024-03' THEN '59112-LeonBlum-Appartement.2024-03.QuittanceLoyer.pdf'
  WHEN '2024-04' THEN '59112-LeonBlum-Appartement.2024-04.QuittanceLoyer.pdf'
  WHEN '2024-05' THEN '59112-LeonBlum-Appartement.2024-05.QuittanceLoyer.pdf'
  WHEN '2024-06' THEN '59112-LeonBlum-Appartement.2024-06.QuittanceLoyer.pdf'
  WHEN '2024-07' THEN '59112-LeonBlum-Appartement.2024-07.QuittanceLoyer.pdf'
  WHEN '2024-08' THEN '59112-LeonBlum-Appartement.2024-08.QuittanceLoyer.pdf'
  WHEN '2024-09' THEN '59112-LeonBlum-Appartement.2024-09.QuittanceLoyer.pdf'
  WHEN '2024-10' THEN '59112-LeonBlum-Appartement.2024-10.QuittanceLoyer.pdf'
  WHEN '2024-11' THEN '59112-LeonBlum-Appartement.2024-11.QuittanceLoyer.pdf'
  WHEN '2024-12' THEN '59112-LeonBlum-Appartement.2024-12.QuittanceLoyer.pdf'
  WHEN '2025-01' THEN '59112-LeonBlum-Appartement.2025-01.QuittanceLoyer.pdf'
  WHEN '2025-02' THEN '59112-LeonBlum-Appartement.2025-02.QuittanceLoyer.pdf'
  WHEN '2025-03' THEN '59112-LeonBlum-Appartement.2025-03.QuittanceLoyer.pdf'
  WHEN '2025-04' THEN '59112-LeonBlum-Appartement.2025-04.QuittanceLoyer.pdf'
  WHEN '2025-05' THEN '59112-LeonBlum-Appartement.2025-05.QuittanceLoyer.pdf'
  WHEN '2025-06' THEN '59112-LeonBlum-Appartement.2025-06.QuittanceLoyer.pdf'
  WHEN '2025-07' THEN '59112-LeonBlum-Appartement.2025-07.QuittanceLoyer.pdf'
  WHEN '2025-08' THEN '59112-LeonBlum-Appartement.2025-08.QuittanceLoyer.pdf'
  WHEN '2025-09' THEN '59112-LeonBlum-Appartement.2025-09.QuittanceLoyer.pdf'
  WHEN '2025-10' THEN '59112-LeonBlum-Appartement.2025-10.QuittanceLoyer.pdf'
  WHEN '2025-11' THEN '59112-LeonBlum-Appartement.2025-11.QuittanceLoyer.pdf'
  WHEN '2025-12' THEN '59112-LeonBlum-Appartement.2025-12.QuittanceLoyer.pdf'
  WHEN '2026-01' THEN '59112-LeonBlum-Appartement.2026-01.QuittanceLoyer.pdf'
  WHEN '2026-02' THEN '59112-LeonBlum-Appartement.2026-02.QuittanceLoyer.pdf'
  WHEN '2026-03' THEN '59112-LeonBlum-Appartement.2026-03.QuittanceLoyer.pdf'
  WHEN '2026-04' THEN '59112-LeonBlum-Appartement.2026-04.QuittanceLoyer.pdf'
END
WHERE p.zipCode = 59112
  AND p.name LIKE '%Blum%'
  AND (u.name = 'Appartement' OR u.friendlyName = 'Appartement')
  AND r.placeUnitRoomId IS NULL
  AND r.paid = 1
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN (
    '2023-05','2023-06','2023-07','2023-08','2023-09','2023-10','2023-11','2023-12',
    '2024-01','2024-02','2024-03','2024-04','2024-05','2024-06','2024-07','2024-08',
    '2024-09','2024-10','2024-11','2024-12',
    '2025-01','2025-02','2025-03','2025-04','2025-05','2025-06',
    '2025-07','2025-08','2025-09','2025-10','2025-11','2025-12',
    '2026-01','2026-02','2026-03','2026-04'
  );

-- -----------------------------------------------------------------------------
-- LocalCommercial — non-colocation
-- -----------------------------------------------------------------------------

-- LocalCommercial — QuittanceLoyer (paid=1) — 2023-05 à 2026-04 continu
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '2023-05' THEN '59112-LeonBlum-LocalCommercial.2023-05.QuittanceLoyer.pdf'
  WHEN '2023-06' THEN '59112-LeonBlum-LocalCommercial.2023-06.QuittanceLoyer.pdf'
  WHEN '2023-07' THEN '59112-LeonBlum-LocalCommercial.2023-07.QuittanceLoyer.pdf'
  WHEN '2023-08' THEN '59112-LeonBlum-LocalCommercial.2023-08.QuittanceLoyer.pdf'
  WHEN '2023-09' THEN '59112-LeonBlum-LocalCommercial.2023-09.QuittanceLoyer.pdf'
  WHEN '2023-10' THEN '59112-LeonBlum-LocalCommercial.2023-10.QuittanceLoyer.pdf'
  WHEN '2023-11' THEN '59112-LeonBlum-LocalCommercial.2023-11.QuittanceLoyer.pdf'
  WHEN '2023-12' THEN '59112-LeonBlum-LocalCommercial.2023-12.QuittanceLoyer.pdf'
  WHEN '2024-01' THEN '59112-LeonBlum-LocalCommercial.2024-01.QuittanceLoyer.pdf'
  WHEN '2024-02' THEN '59112-LeonBlum-LocalCommercial.2024-02.QuittanceLoyer.pdf'
  WHEN '2024-03' THEN '59112-LeonBlum-LocalCommercial.2024-03.QuittanceLoyer.pdf'
  WHEN '2024-04' THEN '59112-LeonBlum-LocalCommercial.2024-04.QuittanceLoyer.pdf'
  WHEN '2024-05' THEN '59112-LeonBlum-LocalCommercial.2024-05.QuittanceLoyer.pdf'
  WHEN '2024-06' THEN '59112-LeonBlum-LocalCommercial.2024-06.QuittanceLoyer.pdf'
  WHEN '2024-07' THEN '59112-LeonBlum-LocalCommercial.2024-07.QuittanceLoyer.pdf'
  WHEN '2024-08' THEN '59112-LeonBlum-LocalCommercial.2024-08.QuittanceLoyer.pdf'
  WHEN '2024-09' THEN '59112-LeonBlum-LocalCommercial.2024-09.QuittanceLoyer.pdf'
  WHEN '2024-10' THEN '59112-LeonBlum-LocalCommercial.2024-10.QuittanceLoyer.pdf'
  WHEN '2024-11' THEN '59112-LeonBlum-LocalCommercial.2024-11.QuittanceLoyer.pdf'
  WHEN '2024-12' THEN '59112-LeonBlum-LocalCommercial.2024-12.QuittanceLoyer.pdf'
  WHEN '2025-01' THEN '59112-LeonBlum-LocalCommercial.2025-01.QuittanceLoyer.pdf'
  WHEN '2025-02' THEN '59112-LeonBlum-LocalCommercial.2025-02.QuittanceLoyer.pdf'
  WHEN '2025-03' THEN '59112-LeonBlum-LocalCommercial.2025-03.QuittanceLoyer.pdf'
  WHEN '2025-04' THEN '59112-LeonBlum-LocalCommercial.2025-04.QuittanceLoyer.pdf'
  WHEN '2025-05' THEN '59112-LeonBlum-LocalCommercial.2025-05.QuittanceLoyer.pdf'
  WHEN '2025-06' THEN '59112-LeonBlum-LocalCommercial.2025-06.QuittanceLoyer.pdf'
  WHEN '2025-07' THEN '59112-LeonBlum-LocalCommercial.2025-07.QuittanceLoyer.pdf'
  WHEN '2025-08' THEN '59112-LeonBlum-LocalCommercial.2025-08.QuittanceLoyer.pdf'
  WHEN '2025-09' THEN '59112-LeonBlum-LocalCommercial.2025-09.QuittanceLoyer.pdf'
  WHEN '2025-10' THEN '59112-LeonBlum-LocalCommercial.2025-10.QuittanceLoyer.pdf'
  WHEN '2025-11' THEN '59112-LeonBlum-LocalCommercial.2025-11.QuittanceLoyer.pdf'
  WHEN '2025-12' THEN '59112-LeonBlum-LocalCommercial.2025-12.QuittanceLoyer.pdf'
  WHEN '2026-01' THEN '59112-LeonBlum-LocalCommercial.2026-01.QuittanceLoyer.pdf'
  WHEN '2026-02' THEN '59112-LeonBlum-LocalCommercial.2026-02.QuittanceLoyer.pdf'
  WHEN '2026-03' THEN '59112-LeonBlum-LocalCommercial.2026-03.QuittanceLoyer.pdf'
  WHEN '2026-04' THEN '59112-LeonBlum-LocalCommercial.2026-04.QuittanceLoyer.pdf'
END
WHERE p.zipCode = 59112
  AND p.name LIKE '%Blum%'
  AND (u.name = 'LocalCommercial' OR u.friendlyName = 'LocalCommercial')
  AND r.placeUnitRoomId IS NULL
  AND r.paid = 1
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN (
    '2023-05','2023-06','2023-07','2023-08','2023-09','2023-10','2023-11','2023-12',
    '2024-01','2024-02','2024-03','2024-04','2024-05','2024-06','2024-07','2024-08',
    '2024-09','2024-10','2024-11','2024-12',
    '2025-01','2025-02','2025-03','2025-04','2025-05','2025-06',
    '2025-07','2025-08','2025-09','2025-10','2025-11','2025-12',
    '2026-01','2026-02','2026-03','2026-04'
  );

-- LocalCommercial — AvisEcheance (paid=0) — pas de 2023-05, 2024-02, 2024-04
UPDATE rentReceipts r
  INNER JOIN placesUnits u ON r.placeUnitId = u.id
  INNER JOIN places p ON u.placeId = p.id
SET r.pdfFilename = CASE DATE_FORMAT(r.periodBegin, '%Y-%m')
  WHEN '2023-06' THEN '59112-LeonBlum-LocalCommercial.2023-06.AvisEcheance.pdf'
  WHEN '2023-07' THEN '59112-LeonBlum-LocalCommercial.2023-07.AvisEcheance.pdf'
  WHEN '2023-08' THEN '59112-LeonBlum-LocalCommercial.2023-08.AvisEcheance.pdf'
  WHEN '2023-09' THEN '59112-LeonBlum-LocalCommercial.2023-09.AvisEcheance.pdf'
  WHEN '2023-10' THEN '59112-LeonBlum-LocalCommercial.2023-10.AvisEcheance.pdf'
  WHEN '2023-11' THEN '59112-LeonBlum-LocalCommercial.2023-11.AvisEcheance.pdf'
  WHEN '2023-12' THEN '59112-LeonBlum-LocalCommercial.2023-12.AvisEcheance.pdf'
  WHEN '2024-01' THEN '59112-LeonBlum-LocalCommercial.2024-01.AvisEcheance.pdf'
  WHEN '2024-03' THEN '59112-LeonBlum-LocalCommercial.2024-03.AvisEcheance.pdf'
  WHEN '2024-05' THEN '59112-LeonBlum-LocalCommercial.2024-05.AvisEcheance.pdf'
  WHEN '2024-06' THEN '59112-LeonBlum-LocalCommercial.2024-06.AvisEcheance.pdf'
  WHEN '2024-07' THEN '59112-LeonBlum-LocalCommercial.2024-07.AvisEcheance.pdf'
  WHEN '2024-08' THEN '59112-LeonBlum-LocalCommercial.2024-08.AvisEcheance.pdf'
  WHEN '2024-09' THEN '59112-LeonBlum-LocalCommercial.2024-09.AvisEcheance.pdf'
  WHEN '2024-10' THEN '59112-LeonBlum-LocalCommercial.2024-10.AvisEcheance.pdf'
  WHEN '2024-11' THEN '59112-LeonBlum-LocalCommercial.2024-11.AvisEcheance.pdf'
  WHEN '2024-12' THEN '59112-LeonBlum-LocalCommercial.2024-12.AvisEcheance.pdf'
  WHEN '2025-01' THEN '59112-LeonBlum-LocalCommercial.2025-01.AvisEcheance.pdf'
  WHEN '2025-02' THEN '59112-LeonBlum-LocalCommercial.2025-02.AvisEcheance.pdf'
  WHEN '2025-03' THEN '59112-LeonBlum-LocalCommercial.2025-03.AvisEcheance.pdf'
  WHEN '2025-04' THEN '59112-LeonBlum-LocalCommercial.2025-04.AvisEcheance.pdf'
  WHEN '2025-05' THEN '59112-LeonBlum-LocalCommercial.2025-05.AvisEcheance.pdf'
  WHEN '2025-06' THEN '59112-LeonBlum-LocalCommercial.2025-06.AvisEcheance.pdf'
  WHEN '2025-07' THEN '59112-LeonBlum-LocalCommercial.2025-07.AvisEcheance.pdf'
  WHEN '2025-08' THEN '59112-LeonBlum-LocalCommercial.2025-08.AvisEcheance.pdf'
  WHEN '2025-09' THEN '59112-LeonBlum-LocalCommercial.2025-09.AvisEcheance.pdf'
  WHEN '2025-10' THEN '59112-LeonBlum-LocalCommercial.2025-10.AvisEcheance.pdf'
  WHEN '2025-11' THEN '59112-LeonBlum-LocalCommercial.2025-11.AvisEcheance.pdf'
  WHEN '2025-12' THEN '59112-LeonBlum-LocalCommercial.2025-12.AvisEcheance.pdf'
  WHEN '2026-01' THEN '59112-LeonBlum-LocalCommercial.2026-01.AvisEcheance.pdf'
  WHEN '2026-02' THEN '59112-LeonBlum-LocalCommercial.2026-02.AvisEcheance.pdf'
  WHEN '2026-03' THEN '59112-LeonBlum-LocalCommercial.2026-03.AvisEcheance.pdf'
  WHEN '2026-04' THEN '59112-LeonBlum-LocalCommercial.2026-04.AvisEcheance.pdf'
END
WHERE p.zipCode = 59112
  AND p.name LIKE '%Blum%'
  AND (u.name = 'LocalCommercial' OR u.friendlyName = 'LocalCommercial')
  AND r.placeUnitRoomId IS NULL
  AND r.paid = 0
  AND DATE_FORMAT(r.periodBegin, '%Y-%m') IN (
    '2023-06','2023-07','2023-08','2023-09','2023-10','2023-11','2023-12',
    '2024-01','2024-03','2024-05','2024-06','2024-07','2024-08','2024-09','2024-10',
    '2024-11','2024-12',
    '2025-01','2025-02','2025-03','2025-04','2025-05','2025-06',
    '2025-07','2025-08','2025-09','2025-10','2025-11','2025-12',
    '2026-01','2026-02','2026-03','2026-04'
  );

-- LocalCommercial — AvisEcheance-fin 2024-10 (fichier spécial fin de période)
-- Ce fichier ne correspond pas au schéma standard ; à injecter manuellement si nécessaire.
-- UPDATE rentReceipts SET pdfFilename = '59112-LeonBlum-LocalCommercial.2024-10.AvisEcheance-fin.pdf'
-- WHERE id = <id_à_identifier_manuellement>;

COMMIT;
