-- =========================================================================
-- Rental Management — MySQL schema
-- No FK, camelCase columns, BIGINT auto-increment IDs
-- =========================================================================

-- Users (auth)
CREATE TABLE IF NOT EXISTS `users` (
  `id`                     BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `email`                  VARCHAR(255) NOT NULL,
  `username`               VARCHAR(150),
  `passwordHash`           VARCHAR(255) NOT NULL,
  `tokenKey`               VARCHAR(255),
  `verified`               TINYINT(1) NOT NULL DEFAULT 0,
  `emailVisibility`        TINYINT(1) NOT NULL DEFAULT 0,
  `isAdmin`                TINYINT(1) NOT NULL DEFAULT 0,
  `isWithdraw`             TINYINT(1) NOT NULL DEFAULT 0,
  `name`                   VARCHAR(255),
  `avatar`                 VARCHAR(255),
  `ownerId`                BIGINT UNSIGNED NULL,
  `lastResetSentAt`        DATETIME(3) NULL,
  `lastVerificationSentAt` DATETIME(3) NULL,
  `createdAt`              DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`              DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_email` (`email`),
  UNIQUE KEY `uq_users_username` (`username`),
  KEY `idx_users_ownerId` (`ownerId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Owners
CREATE TABLE IF NOT EXISTS `owners` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`        VARCHAR(255),
  `email`       VARCHAR(255),
  `address`     VARCHAR(500),
  `zipCode`     INT,
  `city`        VARCHAR(255),
  `phoneNumber` VARCHAR(50),
  `iban`        VARCHAR(64),
  `userId`      BIGINT UNSIGNED,
  `createdAt`   DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`   DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_owners_userId` (`userId`),
  KEY `idx_owners_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Places
CREATE TABLE IF NOT EXISTS `places` (
  `id`        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`      VARCHAR(255),
  `address`   VARCHAR(500),
  `zipCode`   INT,
  `city`      VARCHAR(255),
  `ownerId`   BIGINT UNSIGNED,
  `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_places_ownerId` (`ownerId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Places Units
CREATE TABLE IF NOT EXISTS `placesUnits` (
  `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`         VARCHAR(255),
  `level`        VARCHAR(50),
  `flatshare`    TINYINT(1) NOT NULL DEFAULT 0,
  `address`      VARCHAR(500),
  `zipCode`      INT,
  `city`         VARCHAR(255),
  `surfaceArea`  DECIMAL(10,2),
  `placeId`      BIGINT UNSIGNED,
  `friendlyName` VARCHAR(255),
  `createdAt`    DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`    DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_placesUnits_placeId` (`placeId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Places Units Rooms
CREATE TABLE IF NOT EXISTS `placesUnitsRooms` (
  `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`           VARCHAR(255),
  `surfaceArea`    DECIMAL(10,2),
  `placesUnitsId`  BIGINT UNSIGNED,
  `createdAt`      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_pur_placesUnitsId` (`placesUnitsId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tenants
CREATE TABLE IF NOT EXISTS `tenants` (
  `id`                      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `genre`                   ENUM('Mlle','Mme','M','Societe'),
  `firstName`               VARCHAR(150),
  `name`                    VARCHAR(150),
  `email`                   VARCHAR(255),
  `phone`                   VARCHAR(50),
  `billingSameAsRental`     TINYINT(1) NOT NULL DEFAULT 1,
  `billingAddress`          VARCHAR(500),
  `billingZipCode`          INT,
  `billingCity`             VARCHAR(255),
  `billingPhone`            VARCHAR(50),
  `withdrawName`            VARCHAR(255),
  `withdrawDay`             TINYINT NOT NULL DEFAULT 1,
  `placeUnitId`             BIGINT UNSIGNED,
  `placeUnitRoomId`         BIGINT UNSIGNED,
  `sendNoticeOfLeaseRental` TINYINT(1) NOT NULL DEFAULT 0,
  `sendLeaseRental`         TINYINT(1) NOT NULL DEFAULT 0,
  `active`                  TINYINT(1) NOT NULL DEFAULT 1,
  `dateEntrance`            DATETIME(3),
  `dateExit`                DATETIME(3),
  `warantyReceiptId`        BIGINT UNSIGNED,
  `createdAt`               DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`               DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_tenants_placeUnitId` (`placeUnitId`),
  KEY `idx_tenants_active` (`active`),
  KEY `idx_tenants_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Rent Receipts
CREATE TABLE IF NOT EXISTS `rentReceipts` (
  `id`              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `placeUnitId`     BIGINT UNSIGNED,
  `placeUnitRoomId` BIGINT UNSIGNED,
  `tenantId`        BIGINT UNSIGNED,
  `amount`          DECIMAL(12,2),
  `periodBegin`     DATETIME(3),
  `periodEnd`       DATETIME(3),
  `paid`            TINYINT(1) NOT NULL DEFAULT 0,
  `pdfFilename`     VARCHAR(255) NULL DEFAULT NULL,
  `createdAt`       DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`       DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_rr_tenantId` (`tenantId`),
  KEY `idx_rr_placeUnitId` (`placeUnitId`),
  KEY `idx_rr_paid` (`paid`),
  KEY `idx_rr_period` (`periodBegin`, `periodEnd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Rent Receipts Detail
CREATE TABLE IF NOT EXISTS `rentReceiptsDetail` (
  `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `rentReceiptsId` BIGINT UNSIGNED,
  `sortOrder`      INT,
  `description`    VARCHAR(500),
  `price`          DECIMAL(12,2),
  `createdAt`      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_rrd_rentReceiptsId` (`rentReceiptsId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Rents (recurring charges)
CREATE TABLE IF NOT EXISTS `rents` (
  `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `tenantId`       BIGINT UNSIGNED,
  `type`           ENUM('Loyer','Charges','Garantie'),
  `price`          DECIMAL(12,2),
  `dateExpiration` DATETIME(3),
  `active`         TINYINT(1) NOT NULL DEFAULT 1,
  `createdAt`      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_rents_tenantId` (`tenantId`),
  KEY `idx_rents_active` (`active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Rents Fees (one-off fees)
CREATE TABLE IF NOT EXISTS `rentsFees` (
  `id`               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `tenantId`         BIGINT UNSIGNED,
  `applicationMonth` DATETIME(3),
  `description`      VARCHAR(500),
  `subDescription`   VARCHAR(500),
  `price`            DECIMAL(12,2),
  `createdAt`        DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`        DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_rfees_tenantId` (`tenantId`),
  KEY `idx_rfees_applicationMonth` (`applicationMonth`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
