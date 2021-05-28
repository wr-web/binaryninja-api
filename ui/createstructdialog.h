#pragma once

#include <QtWidgets/QDialog>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QCheckBox>
#include "binaryninjaapi.h"
#include "uicontext.h"

class BINARYNINJAUIAPI CreateStructDialog: public QDialog
{
	Q_OBJECT

	QLineEdit* m_name;
	QLineEdit* m_size;
	QCheckBox* m_pointer;

	BinaryViewRef m_view;
	BinaryNinja::QualifiedName m_resultName;
	uint64_t m_resultSize;
	bool m_applyAsPointer;

public:
	CreateStructDialog(QWidget* parent, BinaryViewRef view, const std::string& name, bool askForApplyAsPointer = false,
		bool applyAsPointer = true);

	BinaryNinja::QualifiedName getName() { return m_resultName; }
	uint64_t getSize() { return m_resultSize; }
	bool applyAsPointer() { return m_applyAsPointer; }

private Q_SLOTS:
	void createStruct();

protected:
	virtual void showEvent(QShowEvent* e) override;

};
