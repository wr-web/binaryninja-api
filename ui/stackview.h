#pragma once

#include <QtWidgets/QAbstractScrollArea>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QDialog>
#include <QtWidgets/QLineEdit>

#include "dockhandler.h"
#include "render.h"
#include "uitypes.h"

class BINARYNINJAUIAPI CreateStackVariableDialog : public QDialog {
    Q_OBJECT

    BinaryViewRef m_data;
    FunctionRef m_func;

    QLineEdit* m_offsetField;
    QLineEdit* m_nameField;
    QComboBox* m_typeDropdown;

protected:
    void accept();

public:
    CreateStackVariableDialog(QWidget* parent, BinaryViewRef data,
        FunctionRef func);
};

class BINARYNINJAUIAPI StackView : public QAbstractScrollArea, public View, public DockContextHandler {
    Q_OBJECT
    Q_INTERFACES(DockContextHandler)

    ViewFrame* m_view;
    BinaryViewRef m_data;
    FunctionRef m_func;
    RenderContext m_renderer;

    std::vector<BinaryNinja::DisassemblyTextLine> m_lines;
    HighlightTokenState m_highlight;

    void rebuildLines();

protected:
    void paintEvent(QPaintEvent* event);
    void mousePressEvent(QMouseEvent* event);

public:
    StackView(ViewFrame* view, BinaryViewRef data);

    //! Refresh the stack view's content.
    void refresh();

    void moveCursorToMouse(QMouseEvent* event, bool isSelecting);

    // --- View Interface ---
    BinaryViewRef getData();
    uint64_t getCurrentOffset();
    void setSelectionOffsets(BNAddressRange range);
    bool navigate(uint64_t offset);
    QFont getFont();
};